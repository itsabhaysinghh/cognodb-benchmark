import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from benchmark.query_engine import QueryBenchmarkEngine
from benchmark.validation import DatasetValidator
from databases import get_adapter

def main():
    validator = DatasetValidator(project_root)
    valid_dataset, dataset_info = validator.validate()
    if not valid_dataset:
        print(f"Error: Dataset verification failed prior to benchmark: {dataset_info}", flush=True)
        sys.exit(1)

    print("Dataset verification passed: SNAP Wiki-Vote (7115 nodes, 103689 relationships)", flush=True)

    databases = ["cognodb", "neo4j", "memgraph", "falkordb", "arangodb"]
    nodes_csv = str(project_root / "data" / "processed" / "nodes.csv")
    rels_csv = str(project_root / "data" / "processed" / "relationships.csv")

    engine = QueryBenchmarkEngine(project_root=project_root)
    final_results = {}

    total_measured_queries = 0
    total_warmup_queries = 0
    total_successes = 0
    total_failures = 0

    for db_key in databases:
        print(f"\n==========================================", flush=True)
        print(f"Preparing {db_key.upper()} for FINAL Phase 7 Benchmarks...", flush=True)
        print(f"==========================================", flush=True)

        adapter = get_adapter(db_key)
        if not adapter.is_configured():
            print(f"Skipping {db_key}: Not configured", flush=True)
            continue

        try:
            adapter.connect()
            adapter.cleanup()
            adapter.create_schema()
            adapter.create_indexes()

            print(f"Loading canonical dataset into {adapter.name}...", flush=True)
            adapter.load_nodes(nodes_csv, batch_size=1000)
            adapter.load_relationships(rels_csv, batch_size=1000)

            valid_load, load_details = adapter.validate_load(7115, 103689)
            if not valid_load:
                print(f"Dataset load validation failed for {db_key}: {load_details}", flush=True)
                continue

            print(f"Executing 6 Workloads × 100 Iterations (10 Warm-ups) on {adapter.name}...", flush=True)
            workload_res = engine.run_query_benchmark_for_adapter(
                adapter,
                db_key,
                warmup_runs=10,
                iterations=100
            )

            db_measured = sum(stats.get("total_queries", 0) for stats in workload_res.values())
            db_warmup = 6 * 10
            db_success = sum(stats.get("success_count", 0) for stats in workload_res.values())
            db_fail = sum(stats.get("fail_count", 0) for stats in workload_res.values())

            total_measured_queries += db_measured
            total_warmup_queries += db_warmup
            total_successes += db_success
            total_failures += db_fail

            final_results[db_key] = {
                "database": adapter.name,
                "version": adapter.get_database_info().get("version", "unknown"),
                "total_measured_queries": db_measured,
                "total_warmup_queries": db_warmup,
                "success_count": db_success,
                "fail_count": db_fail,
                "workloads": workload_res
            }
            print(f"Final Phase 7 query benchmarks completed for {adapter.name}", flush=True)

            adapter.cleanup()

        except Exception as e:
            print(f"Error during final query benchmark for {db_key}: {e}", flush=True)
        finally:
            adapter.disconnect()

    summary_file = project_root / "results" / "processed" / "query_benchmark_final_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "benchmark_phase": "Phase 7 Final",
            "total_databases": len(final_results),
            "total_measured_queries": total_measured_queries,
            "total_warmup_queries": total_warmup_queries,
            "total_successes": total_successes,
            "total_failures": total_failures,
            "results": final_results
        }, f, indent=2)

    print("\n" + "=" * 90, flush=True)
    print("FINAL PHASE 7 GRAPH QUERY & TRAVERSAL BENCHMARK COMPLETE", flush=True)
    print("=" * 90, flush=True)
    print(json.dumps(final_results, indent=2), flush=True)

if __name__ == "__main__":
    main()
