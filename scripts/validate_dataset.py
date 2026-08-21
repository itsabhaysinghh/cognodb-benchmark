import gzip
import os
import sys
from pathlib import Path

def resolve_dataset_path():
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    project_root = Path(__file__).resolve().parent.parent
    gz_path = project_root / "data" / "raw" / "Wiki-Vote.txt.gz"
    txt_path = project_root / "data" / "raw" / "Wiki-Vote.txt"
    if gz_path.exists():
        return gz_path
    if txt_path.exists():
        return txt_path
    return gz_path

def validate(file_path: Path):
    if not file_path.exists():
        print(f"Error: Dataset file not found at {file_path}", file=sys.stderr)
        sys.exit(1)

    is_gz = file_path.suffix == ".gz" or str(file_path).endswith(".tar.gz")
    open_fn = (lambda: gzip.open(file_path, "rt", encoding="utf-8", errors="replace")) if is_gz else (lambda: open(file_path, "r", encoding="utf-8", errors="replace"))

    unique_nodes = set()
    unique_sources = set()
    unique_targets = set()
    seen_edges = set()

    valid_edge_count = 0
    malformed_line_count = 0
    duplicate_edge_count = 0
    self_loop_count = 0
    sample_edges = []

    with open_fn() as f:
        for line_num, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                continue

            parts = line_str.split()
            if len(parts) != 2:
                malformed_line_count += 1
                continue

            src, dst = parts[0], parts[1]
            if not src.isdigit() or not dst.isdigit():
                malformed_line_count += 1
                continue

            src_id = int(src)
            dst_id = int(dst)

            if len(sample_edges) < 5:
                sample_edges.append((src_id, dst_id))

            if src_id == dst_id:
                self_loop_count += 1

            edge = (src_id, dst_id)
            if edge in seen_edges:
                duplicate_edge_count += 1
            else:
                seen_edges.add(edge)

            unique_sources.add(src_id)
            unique_targets.add(dst_id)
            unique_nodes.add(src_id)
            unique_nodes.add(dst_id)
            valid_edge_count += 1

    rel_path = file_path.as_posix()
    project_root_str = Path(__file__).resolve().parent.parent.as_posix()
    if rel_path.startswith(project_root_str):
        rel_path = rel_path[len(project_root_str):].lstrip("/")

    print("Dataset validation")
    print(f"File: {rel_path}")
    print(f"Nodes: {len(unique_nodes)}")
    print(f"Relationships: {len(seen_edges)}")
    print(f"Valid edges: {valid_edge_count}")
    print(f"Malformed lines: {malformed_line_count}")
    print(f"Duplicate edges: {duplicate_edge_count}")
    print(f"Self-loops: {self_loop_count}")
    print("Graph type: directed")
    if sample_edges:
        print("Sample edges:")
        for s, d in sample_edges:
            print(f"  {s} -> {d}")

if __name__ == "__main__":
    target_path = resolve_dataset_path()
    validate(target_path)
