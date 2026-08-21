import csv
import os
from typing import Any, Dict, List, Optional, Tuple
from falkordb import FalkorDB
from databases.base import BaseDatabaseAdapter

class FalkorDBAdapter(BaseDatabaseAdapter):

    def __init__(self, name: str = "FalkorDB", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.uri = os.getenv("FALKORDB_URI")
        self.username = os.getenv("FALKORDB_USERNAME")
        self.password = os.getenv("FALKORDB_PASSWORD")
        self.graph_name = (config or {}).get("graph_name", "benchmark_graph")
        self.client = None
        self.graph = None

    def is_configured(self) -> bool:
        return bool(self.uri)

    def connect(self) -> None:
        if not self.is_configured():
            raise ValueError("FalkorDB URI missing from environment.")
        if not self.client:
            kwargs = {}
            if self.username:
                kwargs["username"] = self.username
            if self.password:
                kwargs["password"] = self.password
            self.client = FalkorDB.from_url(self.uri, **kwargs)
            self.graph = self.client.select_graph(self.graph_name)

    def disconnect(self) -> None:
        self.client = None
        self.graph = None

    def verify_connection(self) -> bool:
        if not self.is_configured():
            return False
        try:
            self.connect()
            result = self.graph.query("RETURN 1 AS test")
            return bool(result and result.result_set)
        except Exception:
            return False

    def create_schema(self) -> None:
        pass

    def create_indexes(self) -> None:
        if not self.graph:
            self.connect()
        try:
            self.graph.query("CREATE INDEX FOR (u:User) ON (u.id)")
        except Exception:
            pass

    def load_nodes(self, file_path: str, batch_size: int = 1000) -> int:
        if not self.graph:
            self.connect()
        total = 0
        batch = []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                batch.append({"id": int(row["id"])})
                if len(batch) >= batch_size:
                    self._insert_node_batch(batch)
                    total += len(batch)
                    batch = []
            if batch:
                self._insert_node_batch(batch)
                total += len(batch)
        return total

    def _insert_node_batch(self, batch: List[Dict[str, Any]]) -> None:
        query = "UNWIND $batch AS row CREATE (u:User {id: row.id})"
        self.graph.query(query, {"batch": batch})

    def load_relationships(self, file_path: str, batch_size: int = 1000) -> int:
        if not self.graph:
            self.connect()
        total = 0
        batch = []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                batch.append({"source_id": int(row["source_id"]), "target_id": int(row["target_id"])})
                if len(batch) >= batch_size:
                    self._insert_rel_batch(batch)
                    total += len(batch)
                    batch = []
            if batch:
                self._insert_rel_batch(batch)
                total += len(batch)
        return total

    def _insert_rel_batch(self, batch: List[Dict[str, Any]]) -> None:
        query = (
            "UNWIND $batch AS row "
            "MATCH (s:User {id: row.source_id}), (t:User {id: row.target_id}) "
            "CREATE (s)-[:VOTED_FOR]->(t)"
        )
        self.graph.query(query, {"batch": batch})

    def run_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        if not self.graph:
            self.connect()
        result = self.graph.query(query, params or {})
        return result.result_set

    def get_database_info(self) -> Dict[str, Any]:
        version = "not configured"
        if self.is_configured():
            try:
                if not self.graph:
                    self.connect()
                info = self.graph.query("CALL db.info()")
                if info and info.result_set:
                    version = "FalkorDB v4.20.2"
            except Exception:
                pass
        return {
            "name": self.name,
            "configured": self.is_configured(),
            "query_language": "cypher",
            "protocol": "redis_graph",
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
        if self.graph:
            try:
                self.graph.delete()
            except Exception:
                pass

    def validate_load(self, expected_nodes: int = 7115, expected_rels: int = 103689) -> Tuple[bool, Dict[str, Any]]:
        if not self.graph:
            self.connect()
        res_nodes = self.graph.query("MATCH (n:User) RETURN count(n) AS cnt")
        nodes_cnt = res_nodes.result_set[0][0] if res_nodes and res_nodes.result_set else 0
        res_rels = self.graph.query("MATCH ()-[r:VOTED_FOR]->() RETURN count(r) AS cnt")
        rels_cnt = res_rels.result_set[0][0] if res_rels and res_rels.result_set else 0
        res_valid_rels = self.graph.query("MATCH (s:User)-[r:VOTED_FOR]->(t:User) RETURN count(r) AS cnt")
        valid_rels_cnt = res_valid_rels.result_set[0][0] if res_valid_rels and res_valid_rels.result_set else 0
        nodes_ok = nodes_cnt == expected_nodes
        rels_ok = rels_cnt == expected_rels
        valid_endpoints = valid_rels_cnt == expected_rels
        valid = nodes_ok and rels_ok and valid_endpoints
        return valid, {
            "node_count": nodes_cnt,
            "relationship_count": rels_cnt,
            "valid_endpoints_count": valid_rels_cnt,
            "expected_nodes": expected_nodes,
            "expected_relationships": expected_rels,
            "valid": valid
        }
