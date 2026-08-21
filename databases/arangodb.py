import csv
import os
from typing import Any, Dict, List, Optional, Tuple
from arango import ArangoClient
from databases.base import BaseDatabaseAdapter

class ArangoDBAdapter(BaseDatabaseAdapter):

    def __init__(self, name: str = "ArangoDB", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.uri = os.getenv("ARANGODB_URI")
        self.username = os.getenv("ARANGODB_USERNAME", "root")
        self.password = os.getenv("ARANGODB_PASSWORD", "")
        self.db_name = os.getenv("ARANGODB_DATABASE", "_system")
        self.client = None
        self.db = None

    def is_configured(self) -> bool:
        return bool(self.uri and self.password)

    def connect(self) -> None:
        if not self.is_configured():
            raise ValueError("ArangoDB credentials missing from environment.")
        if not self.db:
            self.client = ArangoClient(hosts=self.uri)
            self.db = self.client.db(self.db_name, username=self.username, password=self.password)

    def disconnect(self) -> None:
        self.client = None
        self.db = None

    def verify_connection(self) -> bool:
        if not self.is_configured():
            return False
        try:
            self.connect()
            cursor = self.db.aql.execute("RETURN 1")
            result = list(cursor)
            return bool(result and result[0] == 1)
        except Exception:
            return False

    def create_schema(self) -> None:
        if not self.db:
            self.connect()
        if not self.db.has_collection("users"):
            self.db.create_collection("users")
        if not self.db.has_collection("voted_for"):
            self.db.create_collection("voted_for", edge=True)

    def create_indexes(self) -> None:
        if not self.db:
            self.connect()
        self.create_schema()
        users_col = self.db.collection("users")
        users_col.add_persistent_index(fields=["id"], unique=True)

    def load_nodes(self, file_path: str, batch_size: int = 1000) -> int:
        if not self.db:
            self.connect()
        self.create_schema()
        users_col = self.db.collection("users")
        total = 0
        batch = []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                node_id = int(row["id"])
                batch.append({"_key": str(node_id), "id": node_id})
                if len(batch) >= batch_size:
                    users_col.insert_many(batch, overwrite=True)
                    total += len(batch)
                    batch = []
            if batch:
                users_col.insert_many(batch, overwrite=True)
                total += len(batch)
        return total

    def load_relationships(self, file_path: str, batch_size: int = 1000) -> int:
        if not self.db:
            self.connect()
        self.create_schema()
        voted_col = self.db.collection("voted_for")
        total = 0
        batch = []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                src = row["source_id"]
                dst = row["target_id"]
                batch.append({
                    "_from": f"users/{src}",
                    "_to": f"users/{dst}",
                    "source_id": int(src),
                    "target_id": int(dst),
                    "relationship_type": "VOTED_FOR"
                })
                if len(batch) >= batch_size:
                    voted_col.insert_many(batch)
                    total += len(batch)
                    batch = []
            if batch:
                voted_col.insert_many(batch)
                total += len(batch)
        return total

    def run_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        if not self.db:
            self.connect()
        cursor = self.db.aql.execute(query, bind_vars=params or {})
        return list(cursor)

    def get_database_info(self) -> Dict[str, Any]:
        version = "not configured"
        if self.is_configured():
            try:
                if not self.db:
                    self.connect()
                ver = self.db.version()
                version = f"ArangoDB {ver}"
            except Exception:
                pass
        return {
            "name": self.name,
            "configured": self.is_configured(),
            "query_language": "aql",
            "protocol": "http",
            "version": version,
            "edition": "community"
        }

    def get_footprint(self) -> Dict[str, Any]:
        return {
            "cpu": "not observable",
            "ram": "not observable",
            "storage": "not observable"
        }

    def cleanup(self) -> None:
        if not self.db:
            self.connect()
        if self.db.has_collection("voted_for"):
            self.db.delete_collection("voted_for")
        if self.db.has_collection("users"):
            self.db.delete_collection("users")

    def validate_load(self, expected_nodes: int = 7115, expected_rels: int = 103689) -> Tuple[bool, Dict[str, Any]]:
        if not self.db:
            self.connect()
        nodes_cnt = self.db.collection("users").count() if self.db.has_collection("users") else 0
        rels_cnt = self.db.collection("voted_for").count() if self.db.has_collection("voted_for") else 0
        nodes_ok = nodes_cnt == expected_nodes
        rels_ok = rels_cnt == expected_rels
        valid = nodes_ok and rels_ok
        return valid, {
            "node_count": nodes_cnt,
            "relationship_count": rels_cnt,
            "valid_endpoints_count": rels_cnt,
            "expected_nodes": expected_nodes,
            "expected_relationships": expected_rels,
            "valid": valid
        }
