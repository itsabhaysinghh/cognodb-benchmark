import json
import statistics
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from benchmark.ingest import IngestBenchmarkEngine

def main():
    databases = ["cognodb", "neo4j", "memgraph", "falkordb", "arangodb"]
    runs_per_db = 3
    engine = IngestBenchmarkEngine(project_root=project_root)

    all_results = {}

    for db_key in databases:
        db_runs = []
        for run_idx in range(runs_per_db):
            print(f"Executing {db_key.upper()} Run {run_idx + 1}/{runs_per_db}...", flush=True)
            res = engine.run_single_ingest(db_key, batch_size=1000)
            db_runs.append(res)
            print(f"  Run {run_idx + 1} Status: {res.get('status')} | Ingest Time: {res.get('total_ingest_time_ms', 0):.2f} ms", flush=True)
        all_results[db_key] = db_runs

    summary = {}
    print("\n" + "=" * 90)
    print("PHASE 6 CONTROLLED INGEST BENCHMARK SUMMARY (15 TOTAL RUNS)")
    print("=" * 90)

    for db_key, runs in all_results.items():
        passed_runs = [r for r in runs if r.get("status") == "passed"]
        failed_runs = [r for r in runs if r.get("status") != "passed"]

        total_times = [r["total_ingest_time_ms"] for r in passed_runs]
        node_tps = [r["nodes_per_second"] for r in passed_runs]
        rel_tps = [r["relationships_per_second"] for r in passed_runs]
        total_tps = [r["total_records_per_second"] for r in passed_runs]

        mean_time = statistics.mean(total_times) if total_times else 0.0
        median_time = statistics.median(total_times) if total_times else 0.0
        mean_node_tp = statistics.mean(node_tps) if node_tps else 0.0
        mean_rel_tp = statistics.mean(rel_tps) if rel_tps else 0.0
        mean_total_tp = statistics.mean(total_tps) if total_tps else 0.0

        db_name = runs[0].get("database", db_key.capitalize()) if runs else db_key.capitalize()

        summary[db_key] = {
            "database_name": db_name,
            "total_runs": len(runs),
            "successful_runs": len(passed_runs),
            "failed_runs": len(failed_runs),
            "raw_ingest_times_ms": total_times,
            "mean_ingest_time_ms": mean_time,
            "median_ingest_time_ms": median_time,
            "mean_nodes_per_second": mean_node_tp,
            "mean_relationships_per_second": mean_rel_tp,
            "mean_total_records_per_second": mean_total_tp,
            "validation_status": "PASS" if len(passed_runs) == len(runs) else "FAIL",
            "cleanup_status": "PASS" if all(r.get("post_cleanup_verified", False) for r in passed_runs) else "FAIL",
            "runs_detail": runs
        }

    summary_file = project_root / "results" / "processed" / "ingest_benchmark_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
