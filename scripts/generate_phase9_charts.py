import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import matplotlib.pyplot as plt

def main():
    charts_dir = project_root / "results" / "processed" / "phase9" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    ingest_file = project_root / "results" / "processed" / "ingest_benchmark_summary.json"
    query_file = project_root / "results" / "processed" / "query_benchmark_final_summary.json"
    phase8_file = project_root / "results" / "processed" / "phase8" / "concurrency_benchmark_final_summary.json"

    with open(ingest_file, "r", encoding="utf-8") as f:
        ingest_data = json.load(f)

    with open(query_file, "r", encoding="utf-8") as f:
        query_data = json.load(f)

    with open(phase8_file, "r", encoding="utf-8") as f:
        phase8_data = json.load(f)

    plt.style.use('ggplot')
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    db_order = ["cognodb", "neo4j", "memgraph", "falkordb", "arangodb"]
    db_names = ["CognoDB", "Neo4j", "Memgraph", "FalkorDB", "ArangoDB"]

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ingest_times = [ingest_data[db]["mean_ingest_time_ms"] for db in db_order]
    ingest_tps = [ingest_data[db]["mean_relationships_per_second"] for db in db_order]

    ax1.bar(db_names, ingest_times, color='#3498db', alpha=0.8, label="Total Ingest Time (ms)")
    ax1.set_ylabel("Total Ingest Time (ms)", color='#3498db', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='#3498db')

    ax2 = ax1.twinx()
    ax2.plot(db_names, ingest_tps, color='#e74c3c', marker='o', linewidth=3, markersize=8, label="Rel Throughput (rels/sec)")
    ax2.set_ylabel("Ingest Throughput (relationships/sec)", color='#e74c3c', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='#e74c3c')

    plt.title("Phase 6 — Ingestion Performance & Throughput Comparison", fontsize=14, fontweight='bold')
    fig.tight_layout()
    chart1_path = charts_dir / "01_ingest_performance.png"
    plt.savefig(chart1_path, dpi=300)
    plt.close()

    fig, ax = plt.subplots(figsize=(12, 6))
    workloads = ["Q1_POINT_LOOKUP", "Q2_1HOP_TRAVERSAL", "Q3_2HOP_TRAVERSAL", "Q4_3HOP_TRAVERSAL", "Q5_FILTERED_LOOKUP", "Q6_AGGREGATION"]
    w_labels = ["Q1 Point", "Q2 1-Hop", "Q3 2-Hop", "Q4 3-Hop", "Q5 Range", "Q6 Agg"]

    for idx, db in enumerate(db_order):
        means = []
        for w in workloads:
            val = query_data["results"][db]["workloads"][w]["mean_ms"]
            means.append(val)
        ax.plot(w_labels, means, marker='o', linewidth=2, label=db_names[idx], color=colors[idx])

    ax.set_yscale('log')
    ax.set_ylabel("Mean Latency (ms, Log Scale)", fontsize=12)
    ax.set_title("Phase 7 — Graph Query & Traversal Latency Comparison (Log Scale)", fontsize=14, fontweight='bold')
    ax.legend()
    fig.tight_layout()
    chart2_path = charts_dir / "02_query_latency_distribution.png"
    plt.savefig(chart2_path, dpi=300)
    plt.close()

    fig, ax = plt.subplots(figsize=(11, 6))
    concurrency_levels = [1, 2, 4, 8, 16]

    for idx, db in enumerate(db_order):
        tps = []
        for c in concurrency_levels:
            val = phase8_data["results"][db]["workloads"]["CONCURRENT_POINT_LOOKUP"][f"c_{c}"]["throughput_ops_sec"]
            tps.append(val)
        ax.plot(concurrency_levels, tps, marker='s', linewidth=2.5, label=db_names[idx], color=colors[idx])

    ax.set_yscale('log')
    ax.set_xlabel("Concurrency Level (Workers)", fontsize=12)
    ax.set_ylabel("Throughput (ops/sec, Log Scale)", fontsize=12)
    ax.set_title("Phase 8 — Concurrent Point Lookup Throughput Scaling", fontsize=14, fontweight='bold')
    ax.set_xticks(concurrency_levels)
    ax.legend()
    fig.tight_layout()
    chart3_path = charts_dir / "03_concurrency_throughput_scaling.png"
    plt.savefig(chart3_path, dpi=300)
    plt.close()

    fig, ax = plt.subplots(figsize=(11, 6))
    for idx, db in enumerate(db_order):
        p95s = []
        for c in concurrency_levels:
            val = phase8_data["results"][db]["workloads"]["MIXED_READ"][f"c_{c}"]["p95_ms"]
            p95s.append(val)
        ax.plot(concurrency_levels, p95s, marker='^', linewidth=2.5, label=db_names[idx], color=colors[idx])

    ax.set_yscale('log')
    ax.set_xlabel("Concurrency Level (Workers)", fontsize=12)
    ax.set_ylabel("p95 Latency (ms, Log Scale)", fontsize=12)
    ax.set_title("Phase 8 — Mixed Read Workload p95 Latency Scaling", fontsize=14, fontweight='bold')
    ax.set_xticks(concurrency_levels)
    ax.legend()
    fig.tight_layout()
    chart4_path = charts_dir / "04_concurrency_latency_percentiles.png"
    plt.savefig(chart4_path, dpi=300)
    plt.close()

    print("Successfully generated all 4 Phase 9 charts in results/processed/phase9/charts/", flush=True)

if __name__ == "__main__":
    main()
