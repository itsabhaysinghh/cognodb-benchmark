import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseDatabaseAdapter(ABC):

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}

    @abstractmethod
    def is_configured(self) -> bool:
        pass

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def verify_connection(self) -> bool:
        pass

    @abstractmethod
    def create_schema(self) -> None:
        pass

    @abstractmethod
    def create_indexes(self) -> None:
        pass

    @abstractmethod
    def load_nodes(self, file_path: str) -> int:
        pass

    @abstractmethod
    def load_relationships(self, file_path: str) -> int:
        pass

    @abstractmethod
    def run_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        pass

    @abstractmethod
    def get_database_info(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_footprint(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def cleanup(self) -> None:
        pass

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
