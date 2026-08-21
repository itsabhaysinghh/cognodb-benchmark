import csv
import random
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

class ConcurrentWorkloadSampler:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.nodes_csv = project_root / "data" / "processed" / "nodes.csv"
        self.node_ids = self._load_node_ids()

    def _load_node_ids(self) -> List[int]:
        ids = []
        with open(self.nodes_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ids.append(int(row["id"]))
        return ids

    def get_random_node_id(self) -> int:
        return random.choice(self.node_ids)

    def get_random_range_params(self, window: int = 500) -> Tuple[int, int]:
        nid = random.choice(self.node_ids)
        return (nid, nid + window)

    def get_query_for_workload(self, db_key: str, workload: str, op_idx: int) -> Tuple[str, str, Dict[str, Any]]:
        node_id = self.node_ids[op_idx % len(self.node_ids)]
        min_id, max_id = node_id, node_id + 500

        if workload == "CONCURRENT_POINT_LOOKUP":
            if db_key == "arangodb":
                return (
                    "Q1_POINT_LOOKUP",
                    "FOR u IN users FILTER u.id == @node_id RETURN u.id",
                    {"node_id": node_id}
                )
            return (
                "Q1_POINT_LOOKUP",
                "MATCH (u:User {id: $node_id}) RETURN u.id AS id",
                {"node_id": node_id}
            )

        if workload == "CONCURRENT_1HOP":
            if db_key == "arangodb":
                return (
                    "Q2_1HOP",
                    "FOR v IN 1..1 OUTBOUND CONCAT('users/', TO_STRING(@node_id)) voted_for RETURN v.id",
                    {"node_id": node_id}
                )
            return (
                "Q2_1HOP",
                "MATCH (u:User {id: $node_id})-[:VOTED_FOR]->(v:User) RETURN v.id AS id",
                {"node_id": node_id}
            )

        if workload == "MIXED_READ":
            sub_ops = ["lookup", "1hop", "2hop", "filtered", "aggregation"]
            selected = sub_ops[op_idx % len(sub_ops)]

            if db_key == "arangodb":
                if selected == "lookup":
                    return ("Q1_POINT_LOOKUP", "FOR u IN users FILTER u.id == @node_id RETURN u.id", {"node_id": node_id})
                if selected == "1hop":
                    return ("Q2_1HOP", "FOR v IN 1..1 OUTBOUND CONCAT('users/', TO_STRING(@node_id)) voted_for RETURN v.id", {"node_id": node_id})
                if selected == "2hop":
                    return ("Q3_2HOP", "FOR v IN 2..2 OUTBOUND CONCAT('users/', TO_STRING(@node_id)) voted_for RETURN COUNT_DISTINCT(v._key)", {"node_id": node_id})
                if selected == "filtered":
                    return ("Q5_FILTERED", "FOR u IN users FILTER u.id >= @min_id AND u.id <= @max_id COLLECT WITH COUNT INTO cnt RETURN cnt", {"min_id": min_id, "max_id": max_id})
                return ("Q6_AGGREGATION", "FOR v IN 1..1 INBOUND CONCAT('users/', TO_STRING(@node_id)) voted_for COLLECT WITH COUNT INTO cnt RETURN cnt", {"node_id": node_id})

            if selected == "lookup":
                return ("Q1_POINT_LOOKUP", "MATCH (u:User {id: $node_id}) RETURN u.id AS id", {"node_id": node_id})
            if selected == "1hop":
                return ("Q2_1HOP", "MATCH (u:User {id: $node_id})-[:VOTED_FOR]->(v:User) RETURN v.id AS id", {"node_id": node_id})
            if selected == "2hop":
                return ("Q3_2HOP", "MATCH (u:User {id: $node_id})-[:VOTED_FOR*2]->(v:User) RETURN count(DISTINCT v) AS cnt", {"node_id": node_id})
            if selected == "filtered":
                return ("Q5_FILTERED", "MATCH (u:User) WHERE u.id >= $min_id AND u.id <= $max_id RETURN count(u) AS cnt", {"min_id": min_id, "max_id": max_id})
            return ("Q6_AGGREGATION", "MATCH (u:User {id: $node_id})<-[r:VOTED_FOR]-(v:User) RETURN count(r) AS cnt", {"node_id": node_id})

        if workload == "MIXED_READ_WRITE":
            if op_idx % 4 == 0:
                temp_id = 9000000 + op_idx
                if db_key == "arangodb":
                    return ("WRITE_TEMP_USER", "INSERT {_key: TO_STRING(@temp_id), id: @temp_id, is_temp: true} INTO users OPTIONS {overwrite: true}", {"temp_id": temp_id})
                return ("WRITE_TEMP_USER", "CREATE (u:TempUser {id: $temp_id, is_temp: true})", {"temp_id": temp_id})
            return self.get_query_for_workload(db_key, "MIXED_READ", op_idx)

        raise ValueError(f"Unknown workload: {workload}")
