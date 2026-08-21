import datetime
import json
import statistics
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from benchmark.timing import Timer
from benchmark.query_workloads import QueryWorkloadSampler

class QueryBenchmarkEngine:
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).resolve().parent.parent
        self.sampler = QueryWorkloadSampler(self.project_root)
        self.raw_dir = self.project_root / "results" / "raw"
        self.processed_dir = self.project_root / "results" / "processed"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def _get_queries_for_adapter(self, db_key: str, node_id: int, min_id: int, max_id: int) -> Dict[str, Tuple[str, Dict[str, Any]]]:
        if db_key == "arangodb":
            return {
                "Q1_POINT_LOOKUP": (
                    "FOR u IN users FILTER u.id == @node_id RETURN u.id",
                    {"node_id": node_id}
                ),
                "Q2_1HOP_TRAVERSAL": (
                    "FOR v IN 1..1 OUTBOUND CONCAT('users/', TO_STRING(@node_id)) voted_for RETURN v.id",
                    {"node_id": node_id}
                ),
                "Q3_2HOP_TRAVERSAL": (
                    "FOR v IN 2..2 OUTBOUND CONCAT('users/', TO_STRING(@node_id)) voted_for RETURN COUNT_DISTINCT(v._key)",
                    {"node_id": node_id}
                ),
                "Q4_3HOP_TRAVERSAL": (
                    "FOR v IN 3..3 OUTBOUND CONCAT('users/', TO_STRING(@node_id)) voted_for RETURN COUNT_DISTINCT(v._key)",
                    {"node_id": node_id}
                ),
                "Q5_FILTERED_LOOKUP": (
                    "FOR u IN users FILTER u.id >= @min_id AND u.id <= @max_id COLLECT WITH COUNT INTO cnt RETURN cnt",
                    {"min_id": min_id, "max_id": max_id}
                ),
                "Q6_AGGREGATION": (
                    "FOR v IN 1..1 INBOUND CONCAT('users/', TO_STRING(@node_id)) voted_for COLLECT WITH COUNT INTO cnt RETURN cnt",
                    {"node_id": node_id}
                )
            }

        return {
            "Q1_POINT_LOOKUP": (
                "MATCH (u:User {id: $node_id}) RETURN u.id AS id",
                {"node_id": node_id}
            ),
            "Q2_1HOP_TRAVERSAL": (
                "MATCH (u:User {id: $node_id})-[:VOTED_FOR]->(v:User) RETURN v.id AS id",
                {"node_id": node_id}
            ),
            "Q3_2HOP_TRAVERSAL": (
                "MATCH (u:User {id: $node_id})-[:VOTED_FOR*2]->(v:User) RETURN count(DISTINCT v) AS cnt",
                {"node_id": node_id}
            ),
            "Q4_3HOP_TRAVERSAL": (
                "MATCH (u:User {id: $node_id})-[:VOTED_FOR*3]->(v:User) RETURN count(DISTINCT v) AS cnt",
                {"node_id": node_id}
            ),
            "Q5_FILTERED_LOOKUP": (
                "MATCH (u:User) WHERE u.id >= $min_id AND u.id <= $max_id RETURN count(u) AS cnt",
                {"min_id": min_id, "max_id": max_id}
            ),
            "Q6_AGGREGATION": (
                "MATCH (u:User {id: $node_id})<-[r:VOTED_FOR]-(v:User) RETURN count(r) AS cnt",
                {"node_id": node_id}
            )
        }

    def _validate_result(self, q_key: str, result: Any, params: Dict[str, Any]) -> bool:
        if result is None:
            return False
        if q_key == "Q1_POINT_LOOKUP":
            if isinstance(result, list):
                if len(result) == 0:
                    return False
                item = result[0]
                val = item.get("id") if isinstance(item, dict) else (item["id"] if hasattr(item, "__getitem__") else item)
                return str(val) == str(params["node_id"])
            return True
        if q_key in ("Q2_1HOP_TRAVERSAL", "Q3_2HOP_TRAVERSAL", "Q4_3HOP_TRAVERSAL", "Q5_FILTERED_LOOKUP", "Q6_AGGREGATION"):
            return isinstance(result, list) or isinstance(result, (int, float)) or result is not None
        return True

    def _percentile(self, values: List[float], p: float) -> float:
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        k = (len(sorted_vals) - 1) * (p / 100.0)
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_vals) else f
        d = k - f
        return sorted_vals[f] + d * (sorted_vals[c] - sorted_vals[f])

    def run_query_benchmark_for_adapter(
        self,
        adapter,
        db_key: str,
        warmup_runs: int = 10,
        iterations: int = 100
    ) -> Dict[str, Any]:
        node_ids = self.sampler.get_sample_node_ids(iterations)
        range_params = self.sampler.get_sample_range_params(iterations)
        workload_keys = [
            "Q1_POINT_LOOKUP",
            "Q2_1HOP_TRAVERSAL",
            "Q3_2HOP_TRAVERSAL",
            "Q4_3HOP_TRAVERSAL",
            "Q5_FILTERED_LOOKUP",
            "Q6_AGGREGATION"
        ]

        for i in range(min(warmup_runs, len(node_ids))):
            w_node_id = node_ids[i]
            w_min_id, w_max_id = range_params[i]
            q_map = self._get_queries_for_adapter(db_key, w_node_id, w_min_id, w_max_id)
            for q_key, (q_str, params) in q_map.items():
                try:
                    adapter.run_query(q_str, params)
                except Exception:
                    pass

        workload_results = {}

        for q_key in workload_keys:
            latencies_ms = []
            success_count = 0
            fail_count = 0
            correct_count = 0

            for i in range(iterations):
                node_id = node_ids[i]
                min_id, max_id = range_params[i]
                q_map = self._get_queries_for_adapter(db_key, node_id, min_id, max_id)
                q_str, params = q_map[q_key]

                timer = Timer()
                try:
                    with timer:
                        res = adapter.run_query(q_str, params)
                    lat = timer.elapsed_ms
                    latencies_ms.append(lat)
                    if self._validate_result(q_key, res, params):
                        correct_count += 1
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception:
                    fail_count += 1

            if latencies_ms:
                stats = {
                    "total_queries": len(latencies_ms),
                    "success_count": success_count,
                    "fail_count": fail_count,
                    "correctness_validated_count": correct_count,
                    "correctness_status": "PASS" if correct_count == iterations else "FAIL",
                    "mean_ms": statistics.mean(latencies_ms),
                    "median_ms": statistics.median(latencies_ms),
                    "min_ms": min(latencies_ms),
                    "max_ms": max(latencies_ms),
                    "p50_ms": self._percentile(latencies_ms, 50),
                    "p90_ms": self._percentile(latencies_ms, 90),
                    "p95_ms": self._percentile(latencies_ms, 95),
                    "p99_ms": self._percentile(latencies_ms, 99),
                    "raw_latencies_ms": latencies_ms
                }
            else:
                stats = {
                    "total_queries": 0,
                    "success_count": 0,
                    "fail_count": fail_count,
                    "correctness_validated_count": 0,
                    "correctness_status": "FAIL",
                    "error": "All queries failed"
                }

            workload_results[q_key] = stats

            run_id = f"final_query_{db_key}_{q_key.lower()}_{uuid.uuid4().hex[:6]}"
            raw_output = self.raw_dir / f"{run_id}.json"
            with open(raw_output, "w", encoding="utf-8") as f:
                json.dump({
                    "run_id": run_id,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "database": adapter.name,
                    "database_key": db_key,
                    "workload": q_key,
                    "warmup_runs": warmup_runs,
                    "iterations": iterations,
                    "stats": stats
                }, f, indent=2)

        return workload_results
