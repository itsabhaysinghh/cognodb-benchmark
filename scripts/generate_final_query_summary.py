import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def main():
    raw_dir = project_root / "results" / "raw"
    processed_dir = project_root / "results" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    db_map = {
        "cognodb": "CognoDB Cloud",
        "neo4j": "Neo4j",
        "memgraph": "Memgraph",
        "falkordb": "FalkorDB",
        "arangodb": "ArangoDB"
    }

    workloads = [
        "Q1_POINT_LOOKUP",
        "Q2_1HOP_TRAVERSAL",
        "Q3_2HOP_TRAVERSAL",
        "Q4_3HOP_TRAVERSAL",
        "Q5_FILTERED_LOOKUP",
        "Q6_AGGREGATION"
    ]

    results = {}
    total_attempted = 0
    total_warmup = 0
    total_success = 0
    total_fail = 0

    for db_key, db_name in db_map.items():
        db_workloads = {}
        db_attempted = 0
        db_warmup = 0
        db_success = 0
        db_fail = 0

        for w_key in workloads:
            pattern = f"final_query_{db_key}_{w_key.lower()}_*.json"
            files = list(raw_dir.glob(pattern))
            if not files:
                continue

            with open(files[0], "r", encoding="utf-8") as f:
                data = json.load(f)

            stats = data.get("stats", {})
            attempted = data.get("iterations", 100)
            warmup = data.get("warmup_runs", 10)
            success = stats.get("success_count", 0)
            fail = stats.get("fail_count", 0)
            sample_count = len(stats.get("raw_latencies_ms", []))
            timeout_rate = f"{(fail / attempted) * 100:.1f}%"

            db_attempted += attempted
            db_warmup += warmup
            db_success += success
            db_fail += fail

            db_workloads[w_key] = {
                "attempted_queries": attempted,
                "warmup_queries": warmup,
                "successful_queries": success,
                "failed_queries": fail,
                "timeout_rate": timeout_rate,
                "latency_sample_count": sample_count,
                "correctness_validated_count": stats.get("correctness_validated_count", 0),
                "correctness_status": stats.get("correctness_status", "UNKNOWN"),
                "mean_ms": stats.get("mean_ms", 0.0),
                "median_ms": stats.get("median_ms", 0.0),
                "min_ms": stats.get("min_ms", 0.0),
                "max_ms": stats.get("max_ms", 0.0),
                "p50_ms": stats.get("p50_ms", 0.0),
                "p90_ms": stats.get("p90_ms", 0.0),
                "p95_ms": stats.get("p95_ms", 0.0),
                "p99_ms": stats.get("p99_ms", 0.0),
                "raw_latencies_ms": stats.get("raw_latencies_ms", [])
            }

        total_attempted += db_attempted
        total_warmup += db_warmup
        total_success += db_success
        total_fail += db_fail

        results[db_key] = {
            "database": db_name,
            "total_attempted_queries": db_attempted,
            "total_warmup_queries": db_warmup,
            "successful_queries": db_success,
            "failed_queries": db_fail,
            "latency_denominator_methodology": "Calculated strictly from successful query latency samples. Failed executions (timeouts) do not produce timing samples and are tracked separately.",
            "workloads": db_workloads
        }

    summary_file = processed_dir / "query_benchmark_final_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "benchmark_phase": "Phase 7 Final",
            "total_databases": len(results),
            "total_attempted_queries": total_attempted,
            "total_warmup_queries": total_warmup,
            "total_successful_queries": total_success,
            "total_failed_queries": total_fail,
            "latency_denominator_methodology": "Calculated strictly from successful query latency samples. Failed executions (timeouts) do not produce timing samples and are tracked separately.",
            "results": results
        }, f, indent=2)

    print(f"Generated {summary_file} successfully.")

if __name__ == "__main__":
    main()
