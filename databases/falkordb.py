import os
from typing import Any, Dict, Optional
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
        pass

    def load_nodes(self, file_path: str) -> int:
        pass

    def load_relationships(self, file_path: str) -> int:
        pass

    def run_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        if not self.graph:
            self.connect()
        result = self.graph.query(query, params or {})
        return result.result_set

    def get_database_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "configured": self.is_configured(),
            "query_language": "cypher",
            "protocol": "redis_graph",
            "version": "not configured",
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
