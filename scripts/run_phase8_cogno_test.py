import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from benchmark.concurrent_engine import ConcurrentBenchmarkEngine
from databases import get_adapter

def main():
    db_key = "cognodb"
    adapter = get_adapter(db_key)
    if not adapter.is_configured():
        print(f"Error: Database {db_key} is not configured.", flush=True)
        sys.exit(1)

    nodes_csv = str(project_root / "data" / "processed" / "nodes.csv")
    rels_csv = str(project_root / "data" / "processed" / "relationships.csv")

    adapter.connect()
    try:
        valid_load, _ = adapter.validate_load(7115, 103689)
        if not valid_load:
            print("Populating database with canonical dataset...", flush=True)
            adapter.cleanup()
            adapter.create_schema()
            adapter.create_indexes()
            adapter.load_nodes(nodes_csv, batch_size=1000)
            adapter.load_relationships(rels_csv, batch_size=1000)
            valid_after, details = adapter.validate_load(7115, 103689)
            if not valid_after:
                print(f"Failed to populate database: {details}", flush=True)
                sys.exit(1)
    finally:
        adapter.disconnect()

    engine = ConcurrentBenchmarkEngine(project_root=project_root)
    workload = "CONCURRENT_POINT_LOOKUP"
    concurrency_levels = [1, 2, 4]
    test_results = []

    print("=" * 80, flush=True)
    print("PHASE 8 INITIAL TEST RUN — COGNODB CLOUD CONCURRENT POINT LOOKUP", flush=True)
    print("=" * 80, flush=True)

    for c in concurrency_levels:
        print(f"Running {workload} on {db_key.upper()} at concurrency = {c} (10 warm-ups, 100 measured ops)...", flush=True)
        res = engine.run_concurrent_workload(
            db_key=db_key,
            workload=workload,
            concurrency=c,
            warmup_count=10,
            measured_count=100
        )
        test_results.append(res)
        print(f"  Level {c} Complete | Success: {res.get('successful_operations')}/100 | Throughput: {res.get('throughput_ops_sec', 0):.2f} ops/sec | Mean Latency: {res.get('mean_ms', 0):.2f} ms | Integrity: {res.get('canonical_graph_integrity')}", flush=True)

    print("\n" + "=" * 80, flush=True)
    print("PHASE 8 INITIAL COGNODB TEST RESULTS SUMMARY", flush=True)
    print("=" * 80, flush=True)
    print(json.dumps(test_results, indent=2), flush=True)

if __name__ == "__main__":
    main()
