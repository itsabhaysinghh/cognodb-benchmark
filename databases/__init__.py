from databases.base import BaseDatabaseAdapter
from databases.cognodb import CognoDBAdapter
from databases.neo4j import Neo4jAdapter
from databases.memgraph import MemgraphAdapter
from databases.falkordb import FalkorDBAdapter
from databases.arangodb import ArangoDBAdapter

ADAPTER_REGISTRY = {
    "cognodb": CognoDBAdapter,
    "neo4j": Neo4jAdapter,
    "memgraph": MemgraphAdapter,
    "falkordb": FalkorDBAdapter,
    "arangodb": ArangoDBAdapter,
}

def get_adapter(key: str, config: dict = None) -> BaseDatabaseAdapter:
    if key not in ADAPTER_REGISTRY:
        raise ValueError(f"Unknown database adapter key: '{key}'. Available: {list(ADAPTER_REGISTRY.keys())}")
    adapter_class = ADAPTER_REGISTRY[key]
    return adapter_class(config=config)

__all__ = [
    "BaseDatabaseAdapter",
    "CognoDBAdapter",
    "Neo4jAdapter",
    "MemgraphAdapter",
    "FalkorDBAdapter",
    "ArangoDBAdapter",
    "ADAPTER_REGISTRY",
    "get_adapter",
]
