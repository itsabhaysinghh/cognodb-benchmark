import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from benchmark.concurrent_engine import ConcurrentBenchmarkEngine
from benchmark.validation import DatasetValidator
from databases import get_adapter

def main():
    validator = DatasetValidator(project_root)
    valid_dataset, dataset_info = validator.validate()
    if not valid_dataset:
        print(f"Error: Dataset verification failed prior to Phase 8 benchmark: {dataset_info}", flush=True)
        sys.exit(1)

    print("Dataset verification passed: SNAP Wiki-Vote (7115 nodes, 103689 relationships)", flush=True)

    databases = ["cognodb", "neo4j", "memgraph", "falkordb", "arangodb"]
    workloads = [
        "CONCURRENT_POINT_LOOKUP",
        "CONCURRENT_1HOP",
        "MIXED_READ",
        "MIXED_READ_WRITE"
    ]
    concurrency_levels = [1, 2, 4, 8, 16]

    nodes_csv = str(project_root / "data" / "processed" / "nodes.csv")
    rels_csv = str(project_root / "data" / "processed" / "relationships.csv")

    engine = ConcurrentBenchmarkEngine(project_root=project_root)
    final_summary = {}

    total_attempted = 0
    total_warmup = 0
    total_successful = 0
    total_failed = 0

    for db_key in databases:
        print(f"\n==========================================", flush=True)
        print(f"Preparing {db_key.upper()} for Phase 8 Concurrency Benchmarks...", flush=True)
        print(f"==========================================", flush=True)

        adapter = get_adapter(db_key)
        if not adapter.is_configured():
            print(f"Error: Database {db_key} is not configured.", flush=True)
            continue

        adapter.connect()
        try:
            valid_load, details = adapter.validate_load(7115, 103689)
            if not valid_load:
                print(f"Populating {adapter.name} with canonical dataset... ({details})", flush=True)
                adapter.cleanup()
                adapter.create_schema()
                adapter.create_indexes()
                adapter.load_nodes(nodes_csv, batch_size=1000)
                adapter.load_relationships(rels_csv, batch_size=1000)
                valid_after, load_details = adapter.validate_load(7115, 103689)
                if not valid_after:
                    print(f"Failed to populate {adapter.name}: {load_details}", flush=True)
                    continue
        except Exception as e:
            print(f"Error checking/populating dataset for {db_key}: {e}", flush=True)
            continue
        finally:
            adapter.disconnect()

        db_results = {}
        for w_name in workloads:
            w_results = {}
            for c_level in concurrency_levels:
                print(f"  [{db_key.upper()}] Running {w_name} at c={c_level} (10 warm-ups, 100 measured)...", flush=True)
                res = engine.run_concurrent_workload(
                    db_key=db_key,
                    workload=w_name,
                    concurrency=c_level,
                    warmup_count=10,
                    measured_count=100
                )

                attempted = res.get("attempted_operations", 100)
                warmup = res.get("warmup_count", 10)
                success = res.get("successful_operations", 0)
                fail = res.get("failed_operations", 0)

                total_attempted += attempted
                total_warmup += warmup
                total_successful += success
                total_failed += fail

                w_results[f"c_{c_level}"] = res
                print(f"    c={c_level} Complete | Success: {success}/100 | Throughput: {res.get('throughput_ops_sec', 0):.2f} ops/sec | Mean: {res.get('mean_ms', 0):.2f} ms | p95: {res.get('p95_ms', 0):.2f} ms", flush=True)

            db_results[w_name] = w_results

        final_summary[db_key] = {
            "database": adapter.name,
            "version": adapter.get_database_info().get("version", "unknown"),
            "edition": adapter.get_database_info().get("edition", "unknown"),
            "workloads": db_results
        }

    summary_file = project_root / "results" / "processed" / "phase8" / "concurrency_benchmark_final_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "benchmark_phase": "Phase 8 Final",
            "total_databases": len(final_summary),
            "total_attempted_operations": total_attempted,
            "total_warmup_operations": total_warmup,
            "total_successful_operations": total_successful,
            "total_failed_operations": total_failed,
            "latency_denominator_methodology": "Calculated strictly from successful operation latency samples. Failed operations/timeouts do not produce timing samples and are tracked separately.",
            "throughput_methodology": "ops/sec = successful_operations / measured_batch_wall_clock_seconds",
            "results": final_summary
        }, f, indent=2)

    print("\n" + "=" * 90, flush=True)
    print("FULL PHASE 8 CONCURRENCY & MIXED WORKLOAD BENCHMARK COMPLETE", flush=True)
    print("=" * 90, flush=True)
    print(f"Final summary saved to: {summary_file}", flush=True)

if __name__ == "__main__":
    main()
