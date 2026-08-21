import csv
import os
from typing import Any, Dict, List, Optional, Tuple
from neo4j import GraphDatabase
from databases.base import BaseDatabaseAdapter

class Neo4jAdapter(BaseDatabaseAdapter):

    def __init__(self, name: str = "Neo4j", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = None

    def is_configured(self) -> bool:
        return bool(self.uri and self.username and self.password)

    def connect(self) -> None:
        if not self.is_configured():
            raise ValueError("Neo4j credentials missing from environment.")
        if not self.driver:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

    def disconnect(self) -> None:
        if self.driver:
            self.driver.close()
            self.driver = None

    def verify_connection(self) -> bool:
        if not self.is_configured():
            return False
        try:
            self.connect()
            self.driver.verify_connectivity()
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS test")
                record = result.single()
                return bool(record and record["test"] == 1)
        except Exception:
            return False

    def create_schema(self) -> None:
        pass

    def create_indexes(self) -> None:
        if not self.driver:
            self.connect()
        with self.driver.session() as session:
            session.run("CREATE INDEX user_id_index IF NOT EXISTS FOR (u:User) ON (u.id)")

    def load_nodes(self, file_path: str, batch_size: int = 1000) -> int:
        if not self.driver:
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
        with self.driver.session() as session:
            session.run(query, {"batch": batch})

    def load_relationships(self, file_path: str, batch_size: int = 1000) -> int:
        if not self.driver:
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
        with self.driver.session() as session:
            session.run(query, {"batch": batch})

    def run_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        if not self.driver:
            self.connect()
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return list(result)

    def get_database_info(self) -> Dict[str, Any]:
        version = "not configured"
        if self.is_configured():
            try:
                if not self.driver:
                    self.connect()
                with self.driver.session() as session:
                    res = session.run("CALL dbms.components() YIELD name, versions, edition RETURN versions[0] AS version, edition")
                    rec = res.single()
                    if rec:
                        version = f"{rec['version']} ({rec['edition']})"
            except Exception:
                pass
        return {
            "name": self.name,
            "configured": self.is_configured(),
            "query_language": "cypher",
            "protocol": "bolt",
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
        if not self.driver:
            self.connect()
        with self.driver.session() as session:
            session.run("MATCH (n:User) DETACH DELETE n")

    def validate_load(self, expected_nodes: int = 7115, expected_rels: int = 103689) -> Tuple[bool, Dict[str, Any]]:
        if not self.driver:
            self.connect()
        with self.driver.session() as session:
            res_nodes = session.run("MATCH (n:User) RETURN count(n) AS cnt")
            nodes_cnt = res_nodes.single()["cnt"]
            res_rels = session.run("MATCH ()-[r:VOTED_FOR]->() RETURN count(r) AS cnt")
            rels_cnt = res_rels.single()["cnt"]
            res_valid_rels = session.run("MATCH (s:User)-[r:VOTED_FOR]->(t:User) RETURN count(r) AS cnt")
            valid_rels_cnt = res_valid_rels.single()["cnt"]
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
