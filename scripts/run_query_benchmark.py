import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from benchmark.query_engine import QueryBenchmarkEngine
from databases import get_adapter

def main():
    databases = ["cognodb", "neo4j", "memgraph", "falkordb", "arangodb"]
    nodes_csv = str(project_root / "data" / "processed" / "nodes.csv")
    rels_csv = str(project_root / "data" / "processed" / "relationships.csv")

    engine = QueryBenchmarkEngine(project_root=project_root)
    all_query_results = {}

    for db_key in databases:
        print(f"\n==========================================", flush=True)
        print(f"Preparing {db_key.upper()} for Query Benchmarks...", flush=True)
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

            print(f"Loading dataset into {adapter.name}...", flush=True)
            adapter.load_nodes(nodes_csv, batch_size=1000)
            adapter.load_relationships(rels_csv, batch_size=1000)

            valid, details = adapter.validate_load(7115, 103689)
            if not valid:
                print(f"Dataset load validation failed for {db_key}: {details}", flush=True)
                continue

            print(f"Executing Phase 7 Query Workloads on {adapter.name}...", flush=True)
            res = engine.run_query_benchmark_for_adapter(adapter, db_key, warmup_runs=5, iterations=30)
            all_query_results[db_key] = {
                "database": adapter.name,
                "version": adapter.get_database_info().get("version", "unknown"),
                "results": res
            }
            print(f"Query benchmarks completed for {adapter.name}", flush=True)

            adapter.cleanup()

        except Exception as e:
            print(f"Error during query benchmark for {db_key}: {e}", flush=True)
        finally:
            adapter.disconnect()

    summary_file = project_root / "results" / "processed" / "query_benchmark_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(all_query_results, f, indent=2)

    print("\n" + "=" * 90, flush=True)
    print("PHASE 7 QUERY & TRAVERSAL BENCHMARK COMPLETE", flush=True)
    print("=" * 90, flush=True)
    print(json.dumps(all_query_results, indent=2), flush=True)

if __name__ == "__main__":
    main()
