import csv
from pathlib import Path
from typing import Dict, List, Tuple

class QueryWorkloadSampler:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.nodes_csv = project_root / "data" / "processed" / "nodes.csv"
        self.rels_csv = project_root / "data" / "processed" / "relationships.csv"

    def get_sample_node_ids(self, sample_size: int = 100) -> List[int]:
        node_ids = []
        with open(self.nodes_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                node_ids.append(int(row["id"]))
        if len(node_ids) <= sample_size:
            return node_ids
        step = len(node_ids) // sample_size
        return node_ids[::step][:sample_size]

    def get_sample_range_params(self, sample_size: int = 100) -> List[Tuple[int, int]]:
        node_ids = self.get_sample_node_ids(sample_size)
        return [(nid, nid + 500) for nid in node_ids]

    def get_degree_stratified_node_ids(self) -> Dict[str, List[int]]:
        degrees = {}
        with open(self.rels_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                src = int(row["source_id"])
                degrees[src] = degrees.get(src, 0) + 1

        sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
        if not sorted_nodes:
            sample = self.get_sample_node_ids(10)
            return {"high": sample[:3], "medium": sample[3:7], "low": sample[7:]}

        n = len(sorted_nodes)
        high = [x[0] for x in sorted_nodes[:max(1, n // 10)]][:10]
        med = [x[0] for x in sorted_nodes[n // 3 : n // 3 + 10]]
        low = [x[0] for x in sorted_nodes[-10:]]

        return {"high": high, "medium": med, "low": low}
