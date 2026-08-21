import concurrent.futures
import datetime
import json
import statistics
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from benchmark.concurrent_workloads import ConcurrentWorkloadSampler
from benchmark.timing import Timer
from databases import get_adapter

class ConcurrentBenchmarkEngine:
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).resolve().parent.parent
        self.sampler = ConcurrentWorkloadSampler(self.project_root)
        self.raw_dir = self.project_root / "results" / "raw" / "phase8"
        self.processed_dir = self.project_root / "results" / "processed" / "phase8"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def _percentile(self, values: List[float], p: float) -> float:
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        k = (len(sorted_vals) - 1) * (p / 100.0)
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_vals) else f
        d = k - f
        return sorted_vals[f] + d * (sorted_vals[c] - sorted_vals[f])

    def _execute_op_on_adapter(self, adapter, db_key: str, workload: str, op_idx: int) -> Tuple[bool, float, Optional[str]]:
        try:
            sub_key, q_str, params = self.sampler.get_query_for_workload(db_key, workload, op_idx)
            timer = Timer()
            with timer:
                res = adapter.run_query(q_str, params)
            valid = res is not None
            return valid, timer.elapsed_ms, None if valid else "Query returned None"
        except Exception as e:
            return False, 0.0, str(e)

    def run_concurrent_workload(
        self,
        db_key: str,
        workload: str,
        concurrency: int,
        warmup_count: int = 10,
        measured_count: int = 100
    ) -> Dict[str, Any]:
        adapter = get_adapter(db_key)
        if not adapter.is_configured():
            return {
                "status": "failed",
                "error": f"Database {db_key} is not configured"
            }

        adapter.connect()

        try:
            for w_idx in range(warmup_count):
                self._execute_op_on_adapter(adapter, db_key, workload, w_idx)

            latencies_ms = []
            success_count = 0
            fail_count = 0
            timeout_count = 0
            errors = []

            batch_start = time.perf_counter()

            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [
                    executor.submit(self._execute_op_on_adapter, adapter, db_key, workload, idx)
                    for idx in range(measured_count)
                ]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        success, lat, err = future.result()
                        if success:
                            success_count += 1
                            latencies_ms.append(lat)
                        else:
                            fail_count += 1
                            if err and "timeout" in err.lower():
                                timeout_count += 1
                            errors.append(err or "Unknown error")
                    except Exception as ex:
                        fail_count += 1
                        errors.append(str(ex))

            batch_end = time.perf_counter()
            measured_wall_clock_sec = batch_end - batch_start
            throughput_ops_sec = (success_count / measured_wall_clock_sec) if measured_wall_clock_sec > 0 else 0.0

            if latencies_ms:
                mean_ms = statistics.mean(latencies_ms)
                median_ms = statistics.median(latencies_ms)
                min_ms = min(latencies_ms)
                max_ms = max(latencies_ms)
                p50_ms = self._percentile(latencies_ms, 50)
                p90_ms = self._percentile(latencies_ms, 90)
                p95_ms = self._percentile(latencies_ms, 95)
                p99_ms = self._percentile(latencies_ms, 99)
            else:
                mean_ms = median_ms = min_ms = max_ms = p50_ms = p90_ms = p95_ms = p99_ms = 0.0

            if workload == "MIXED_READ_WRITE":
                try:
                    if db_key == "arangodb":
                        adapter.run_query("FOR u IN users FILTER u.is_temp == true REMOVE u IN users")
                    else:
                        adapter.run_query("MATCH (u:TempUser) DETACH DELETE u")
                except Exception:
                    pass

            graph_valid, graph_details = adapter.validate_load(7115, 103689)
            db_info = adapter.get_database_info()

            run_id = f"corrected_phase8_{db_key}_{workload.lower()}_c{concurrency}_{uuid.uuid4().hex[:6]}"

            result_data = {
                "run_id": run_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "database": adapter.name,
                "database_key": db_key,
                "database_version": db_info.get("version", "unknown"),
                "deployment": db_info.get("edition", "unknown"),
                "workload": workload,
                "concurrency": concurrency,
                "warmup_count": warmup_count,
                "measured_count": measured_count,
                "attempted_operations": measured_count,
                "successful_operations": success_count,
                "failed_operations": fail_count,
                "timeouts": timeout_count,
                "timeout_rate": f"{(timeout_count / measured_count) * 100:.1f}%",
                "latency_sample_count": len(latencies_ms),
                "measured_wall_clock_sec": measured_wall_clock_sec,
                "throughput_ops_sec": throughput_ops_sec,
                "min_ms": min_ms,
                "max_ms": max_ms,
                "mean_ms": mean_ms,
                "median_ms": median_ms,
                "p50_ms": p50_ms,
                "p90_ms": p90_ms,
                "p95_ms": p95_ms,
                "p99_ms": p99_ms,
                "correctness_status": "PASS" if (success_count == measured_count and graph_valid) else ("PARTIAL" if graph_valid else "FAIL"),
                "canonical_graph_integrity": "PASS" if graph_valid else "FAIL",
                "graph_details": graph_details,
                "raw_latencies_ms": latencies_ms
            }

            output_file = self.raw_dir / f"raw_{run_id}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result_data, f, indent=2)

            result_data["result_file"] = str(output_file)
            return result_data

        finally:
            adapter.disconnect()
