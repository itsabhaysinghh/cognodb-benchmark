import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Tuple

class DatasetValidator:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.manifest_path = project_root / "data" / "processed" / "dataset_manifest.json"
        self.nodes_path = project_root / "data" / "processed" / "nodes.csv"
        self.relationships_path = project_root / "data" / "processed" / "relationships.csv"

    def _compute_sha256(self, file_path: Path) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _count_csv_rows(self, file_path: Path) -> int:
        count = 0
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for _ in reader:
                count += 1
        return count

    def validate(self) -> Tuple[bool, Dict[str, Any]]:
        if not self.manifest_path.exists():
            return False, {"error": "Manifest file missing"}
        if not self.nodes_path.exists() or not self.relationships_path.exists():
            return False, {"error": "Processed CSV files missing"}

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        nodes_hash = self._compute_sha256(self.nodes_path)
        rels_hash = self._compute_sha256(self.relationships_path)
        nodes_count = self._count_csv_rows(self.nodes_path)
        rels_count = self._count_csv_rows(self.relationships_path)

        hash_valid = (
            nodes_hash == manifest.get("nodes_file_sha256")
            and rels_hash == manifest.get("relationships_file_sha256")
        )
        counts_valid = (
            nodes_count == manifest.get("node_count")
            and rels_count == manifest.get("relationship_count")
        )

        details = {
            "dataset_name": manifest.get("dataset_name"),
            "dataset_hash": nodes_hash[:16] + rels_hash[:16],
            "nodes_hash": nodes_hash,
            "relationships_hash": rels_hash,
            "nodes_count": nodes_count,
            "relationships_count": rels_count,
            "expected_nodes": manifest.get("node_count"),
            "expected_relationships": manifest.get("relationship_count"),
            "valid": hash_valid and counts_valid
        }
        return hash_valid and counts_valid, details

class LoadValidator:
    def __init__(self, adapter):
        self.adapter = adapter

    def validate(self, expected_nodes: int = 7115, expected_rels: int = 103689) -> Tuple[bool, Dict[str, Any]]:
        try:
            valid, details = self.adapter.validate_load(expected_nodes, expected_rels)
            return valid, details
        except Exception as e:
            return False, {"error": str(e)}
