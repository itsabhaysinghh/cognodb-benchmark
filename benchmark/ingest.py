import datetime
import json
import os
import platform
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from benchmark.timing import Timer
from benchmark.validation import DatasetValidator, LoadValidator
from databases import get_adapter

class IngestBenchmarkEngine:
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).resolve().parent.parent
        self.dataset_validator = DatasetValidator(self.project_root)
        self.raw_results_dir = self.project_root / "results" / "raw"
        self.processed_results_dir = self.project_root / "results" / "processed"
        self.raw_results_dir.mkdir(parents=True, exist_ok=True)
        self.processed_results_dir.mkdir(parents=True, exist_ok=True)

    def _get_git_commit(self) -> str:
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=False
            )
            return res.stdout.strip() if res.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def run_single_ingest(self, db_key: str, batch_size: int = 1000) -> Dict[str, Any]:
        valid_dataset, dataset_info = self.dataset_validator.validate()
        if not valid_dataset:
            return {
                "status": "failed",
                "failed_stage": "dataset_validation",
                "error": "Dataset validation failed",
                "dataset_info": dataset_info
            }

        adapter = get_adapter(db_key)
        if not adapter.is_configured():
            return {
                "status": "failed",
                "failed_stage": "environment_check",
                "error": f"Database '{db_key}' is not configured"
            }

        run_id = f"run_{datetime.datetime.now().strftime('%Y%m%m_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        nodes_csv = str(self.project_root / "data" / "processed" / "nodes.csv")
        rels_csv = str(self.project_root / "data" / "processed" / "relationships.csv")

        node_count = dataset_info["nodes_count"]
        rel_count = dataset_info["relationships_count"]

        try:
            adapter.connect()
            adapter.cleanup()

            schema_timer = Timer()
            with schema_timer:
                adapter.create_schema()
            schema_setup_time_ms = schema_timer.elapsed_ms

            index_timer = Timer()
            with index_timer:
                adapter.create_indexes()
            index_setup_time_ms = index_timer.elapsed_ms

            node_timer = Timer()
            with node_timer:
                loaded_nodes = adapter.load_nodes(nodes_csv, batch_size=batch_size)
            node_load_time_ms = node_timer.elapsed_ms

            rel_timer = Timer()
            with rel_timer:
                loaded_rels = adapter.load_relationships(rels_csv, batch_size=batch_size)
            rel_load_time_ms = rel_timer.elapsed_ms

            total_ingest_time_ms = node_load_time_ms + rel_load_time_ms

            load_validator = LoadValidator(adapter)
            load_valid, load_details = load_validator.validate(
                expected_nodes=node_count,
                expected_rels=rel_count
            )

            if not load_valid:
                status = "failed"
                failed_stage = "post_load_validation"
                error_msg = f"Post-load validation failed: {load_details}"
            else:
                status = "passed"
                failed_stage = None
                error_msg = None

            node_load_sec = node_load_time_ms / 1000.0
            rel_load_sec = rel_load_time_ms / 1000.0
            total_ingest_sec = total_ingest_time_ms / 1000.0

            nodes_per_second = node_count / node_load_sec if node_load_sec > 0 else 0.0
            relationships_per_second = rel_count / rel_load_sec if rel_load_sec > 0 else 0.0
            total_records_per_second = (node_count + rel_count) / total_ingest_sec if total_ingest_sec > 0 else 0.0

            db_info = adapter.get_database_info()

            result_data = {
                "run_id": run_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "database": adapter.name,
                "database_key": db_key,
                "database_version": db_info.get("version", "unknown"),
                "deployment": db_info.get("edition", "unknown"),
                "dataset_name": dataset_info.get("dataset_name"),
                "dataset_hash": dataset_info.get("dataset_hash"),
                "client_machine": platform.node(),
                "python_version": sys.version,
                "benchmark_git_commit": self._get_git_commit(),
                "node_count": node_count,
                "relationship_count": rel_count,
                "loaded_nodes": loaded_nodes,
                "loaded_relationships": loaded_rels,
                "batch_size": batch_size,
                "schema_setup_time_ms": schema_setup_time_ms,
                "index_setup_time_ms": index_setup_time_ms,
                "node_load_time_ms": node_load_time_ms,
                "relationship_load_time_ms": rel_load_time_ms,
                "total_ingest_time_ms": total_ingest_time_ms,
                "nodes_per_second": nodes_per_second,
                "relationships_per_second": relationships_per_second,
                "total_records_per_second": total_records_per_second,
                "status": status,
                "failed_stage": failed_stage,
                "error": error_msg,
                "validation_details": load_details
            }

            output_file = self.raw_results_dir / f"ingest_{db_key}_{run_id}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result_data, f, indent=2)

            adapter.cleanup()
            clean_valid, clean_details = adapter.validate_load(0, 0)
            result_data["post_cleanup_verified"] = clean_valid
            result_data["result_file"] = str(output_file)

            return result_data

        except Exception as e:
            return {
                "run_id": run_id,
                "database": db_key,
                "status": "failed",
                "failed_stage": "ingest_execution",
                "error": str(e)
            }
        finally:
            adapter.disconnect()
