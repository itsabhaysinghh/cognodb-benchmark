import csv
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent

def resolve_raw_path(project_root: Path) -> Path:
    gz_path = project_root / "data" / "raw" / "Wiki-Vote.txt.gz"
    txt_path = project_root / "data" / "raw" / "Wiki-Vote.txt"
    if gz_path.exists():
        return gz_path
    if txt_path.exists():
        return txt_path
    return gz_path

def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def normalize():
    project_root = get_project_root()
    raw_path = resolve_raw_path(project_root)

    if not raw_path.exists():
        print(f"Error: Raw dataset not found at {raw_path}", file=sys.stderr)
        sys.exit(1)

    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    nodes_file = processed_dir / "nodes.csv"
    relationships_file = processed_dir / "relationships.csv"
    manifest_file = processed_dir / "dataset_manifest.json"

    is_gz = raw_path.suffix == ".gz" or str(raw_path).endswith(".tar.gz")
    open_fn = (lambda: gzip.open(raw_path, "rt", encoding="utf-8", errors="replace")) if is_gz else (lambda: open(raw_path, "r", encoding="utf-8", errors="replace"))

    nodes_set = set()
    edges = []
    seen_edges = set()

    with open_fn() as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                continue

            parts = line_str.split()
            if len(parts) != 2:
                print(f"Error: Malformed line detected: {line_str}", file=sys.stderr)
                sys.exit(1)

            src_str, dst_str = parts[0], parts[1]
            if not src_str.isdigit() or not dst_str.isdigit():
                print(f"Error: Non-numeric node ID detected: {line_str}", file=sys.stderr)
                sys.exit(1)

            src = int(src_str)
            dst = int(dst_str)

            if src == dst:
                print(f"Error: Unexpected self-loop detected: {src} -> {dst}", file=sys.stderr)
                sys.exit(1)

            edge = (src, dst)
            if edge in seen_edges:
                print(f"Error: Unexpected duplicate edge detected: {src} -> {dst}", file=sys.stderr)
                sys.exit(1)

            seen_edges.add(edge)
            edges.append(edge)
            nodes_set.add(src)
            nodes_set.add(dst)

    sorted_nodes = sorted(nodes_set)
    sorted_edges = sorted(edges, key=lambda e: (e[0], e[1]))

    with open(nodes_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id"])
        for node_id in sorted_nodes:
            writer.writerow([node_id])

    with open(relationships_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source_id", "target_id", "relationship_type"])
        for src, dst in sorted_edges:
            writer.writerow([src, dst, "VOTED_FOR"])

    loaded_nodes = set()
    with open(nodes_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        if header != ["id"]:
            print("Validation failure: nodes.csv header is incorrect", file=sys.stderr)
            sys.exit(1)
        for row in reader:
            loaded_nodes.add(int(row[0]))

    if len(loaded_nodes) != len(sorted_nodes):
        print(f"Validation failure: Node count mismatch ({len(loaded_nodes)} != {len(sorted_nodes)})", file=sys.stderr)
        sys.exit(1)

    loaded_rel_count = 0
    with open(relationships_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        if header != ["source_id", "target_id", "relationship_type"]:
            print("Validation failure: relationships.csv header is incorrect", file=sys.stderr)
            sys.exit(1)
        for row in reader:
            src = int(row[0])
            dst = int(row[1])
            rel_type = row[2]
            if rel_type != "VOTED_FOR":
                print(f"Validation failure: Invalid relationship type '{rel_type}'", file=sys.stderr)
                sys.exit(1)
            if src not in loaded_nodes:
                print(f"Validation failure: source_id {src} not found in nodes", file=sys.stderr)
                sys.exit(1)
            if dst not in loaded_nodes:
                print(f"Validation failure: target_id {dst} not found in nodes", file=sys.stderr)
                sys.exit(1)
            loaded_rel_count += 1

    if loaded_rel_count != len(sorted_edges):
        print(f"Validation failure: Relationship count mismatch ({loaded_rel_count} != {len(sorted_edges)})", file=sys.stderr)
        sys.exit(1)

    raw_rel_path = raw_path.relative_to(project_root).as_posix()
    manifest_data = {
        "dataset_name": "SNAP Wiki-Vote",
        "source": "Stanford SNAP",
        "raw_file": raw_rel_path,
        "node_count": len(sorted_nodes),
        "relationship_count": len(sorted_edges),
        "graph_type": "directed",
        "relationship_type": "VOTED_FOR",
        "validation_status": "passed",
        "raw_file_sha256": compute_sha256(raw_path),
        "nodes_file_sha256": compute_sha256(nodes_file),
        "relationships_file_sha256": compute_sha256(relationships_file)
    }

    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    print("Dataset normalization completed successfully.")
    print(f"Nodes: {manifest_data['node_count']}")
    print(f"Relationships: {manifest_data['relationship_count']}")
    print(f"Validation status: {manifest_data['validation_status']}")
    print("Files created:")
    print(f"  data/processed/nodes.csv (SHA-256: {manifest_data['nodes_file_sha256']})")
    print(f"  data/processed/relationships.csv (SHA-256: {manifest_data['relationships_file_sha256']})")
    print(f"  data/processed/dataset_manifest.json (Raw SHA-256: {manifest_data['raw_file_sha256']})")

if __name__ == "__main__":
    normalize()
