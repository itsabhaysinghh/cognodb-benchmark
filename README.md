# Comparative Graph Database Benchmark

## Overview
This repository provides a reproducible, empirical benchmark comparing five graph database systems: **CognoDB Cloud**, **Neo4j**, **Memgraph**, **FalkorDB**, and **ArangoDB**.

The evaluation uses the canonical **SNAP Wiki-Vote dataset** comprising **7,115 User nodes** and **103,689 directed VOTED_FOR relationships**.

The framework benchmarks performance across three core areas: data ingestion throughput, single-threaded graph query and traversal latencies, and multi-worker concurrent throughput scaling.

---

## Benchmark Scope

| Benchmark Phase | Scope & Objective | Key Metrics Captured |
| :--- | :--- | :--- |
| **Phase 6 — Ingestion** | Bulk loading of nodes and relationships across 3 clean runs per database. | Schema time, index time, node load, relationship load, total time, rel/sec throughput. |
| **Phase 7 — Query & Traversal** | Single-threaded execution of 6 workloads (Q1-Q6) across 100 iterations + 10 warm-ups. | Mean, median/p50, p90, p95, p99, min, max, success rate, query correctness. |
| **Phase 8 — Concurrency** | Multi-worker execution across 4 workloads and 5 concurrency levels (c=1, 2, 4, 8, 16). | Throughput (ops/sec), p50/p95 latency scaling, success rate, graph state integrity. |
| **Phase 9 — Comparative Analysis** | Neutral workload-specific comparative analysis, charts, and publication PDF report. | High-res PNG charts, final report Markdown, ReportLab publication PDF report. |
| **Phase 10 — Security & Release** | Verification of dataset hashes, secret scanning, dependency pinning, and release audit. | Release gate verification matrix, security audit report, reproducibility manifest. |

---

## Key Results

Based strictly on empirical execution data from the authoritative benchmark results:

- **Ingestion Throughput**: **ArangoDB** achieved the highest measured relationship ingestion throughput (**42,705.60 rels/sec**).
- **Single-Threaded Query Latency**: **FalkorDB** achieved the lowest measured latency in the tested single-threaded workloads (**0.49 ms** Q1 point lookup, **0.95 ms** Q4 3-hop traversal).
- **Concurrent Point-Lookup Throughput**: **Memgraph** achieved the highest measured throughput in the tested concurrent point-lookup workload (**15,622.75 ops/sec** at c=16).
- **Managed Cloud & Remote Effects**: **CognoDB Cloud** exhibited an observed latency floor of approximately 250 ms in this experiment, which includes WAN/network transmission overhead.
- **Reliability & Timeouts**: CognoDB Cloud achieved 100% successful execution across the Phase 8 concurrency benchmark, while Phase 7 recorded 88/100 successful executions for Q4 3-hop traversal, with 12 timeouts over WAN.

*Note: In accordance with scientific methodology, no universal "overall winner" is assigned because performance varies by workload and deployment architecture.*

---

## Environment

- **Client Environment**: LAPTOP-2ID0MJRR (Windows 11 Enterprise x64)
- **Python Version**: Python 3.12.10 x64
- **Container Isolation**: Docker Compose
- **Resource Constraints**:
  - **CPU Limit**: Enforced at `0.50 vCPU` for local containers (`deploy.resources.limits`).
  - **RAM Limit**: Enforced at `256 MB RAM` for Memgraph, FalkorDB, and ArangoDB. Neo4j required a verified minimum limit of `768 MB RAM` due to Java JVM heap and metaspace operational requirements.
  - **Storage Allocation**: Configured at `1.0 GB` data directory volume allocation.

---

## Repository Structure

```
cognodb-benchmark/
├── benchmark/              # Core timing, validation, query, and concurrency engines
├── databases/              # Adapter implementations (CognoDB, Neo4j, Memgraph, FalkorDB, ArangoDB)
├── scripts/                # Verification, benchmark execution, and report generation scripts
├── config/                 # Fairness records and database parameters
├── data/                   # Raw and normalized SNAP Wiki-Vote dataset files
├── results/                # Raw JSON execution logs and processed benchmark summaries
│   ├── raw/
│   └── processed/
├── reports/                # Security audit and Wexa AI compliance reports
├── docker-compose.yml      # Local container orchestration with resource limits
├── requirements.txt        # Pinned Python dependencies
├── .env.example            # Environment configuration template with placeholders
└── Comparative_Graph_Database_Benchmark_Report.pdf  # Authoritative publication PDF
```

---

## Requirements

- **Python**: Version 3.12 or higher
- **Docker**: Docker Desktop with Docker Compose V2 support
- **Git**: Git 2.30 or higher

---

## Configuration

Copy `.env.example` to create your local `.env` file:

```bash
cp .env.example .env
```

Define database endpoints and connection credentials in `.env`:
- `COGNODB_URI`, `COGNODB_USERNAME`, `COGNODB_PASSWORD`
- `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`
- `MEMGRAPH_URI`, `MEMGRAPH_USERNAME`, `MEMGRAPH_PASSWORD`
- `FALKORDB_URI`, `FALKORDB_USERNAME`, `FALKORDB_PASSWORD`
- `ARANGODB_URI`, `ARANGODB_USERNAME`, `ARANGODB_PASSWORD`, `ARANGODB_DATABASE`

*Security Note: `.env` is ignored by Git and must never be committed. `.env.example` contains placeholders only.*

---

## Running the Benchmark

Follow this copy-pasteable execution sequence:

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Local Database Containers
```bash
docker compose up -d
```

### 3. Verify Container Resource Limits
```bash
python scripts/verify_resource_limits.py
```

### 4. Verify Database Connections
```bash
python scripts/check_database_environments.py
```

### 5. Execute Phase 6 (Ingestion Benchmark)
```bash
python scripts/run_full_benchmark.py
```

### 6. Execute Phase 7 (Single-Threaded Query Benchmark)
```bash
python scripts/run_final_query_benchmark.py
```

### 7. Execute Phase 8 (Concurrency Benchmark)
```bash
python scripts/run_full_phase8_benchmark.py
```

### 8. Generate Phase 9 Charts & Reports
```bash
python scripts/generate_phase9_charts.py
python scripts/generate_audited_final_report.py
python scripts/generate_walkthrough_pdf.py
```

---

## Results & Reports

Authoritative benchmark outputs are located in:

- **Processed JSON Summaries**: [`results/processed/`](file:///d:/New%20folder/cognodb-benchmark/results/processed/)
  - Ingestion Summary: `ingest_benchmark_summary.json`
  - Query Summary: `query_benchmark_final_summary.json`
  - Concurrency Summary: `phase8/concurrency_benchmark_final_summary.json`
- **Raw Execution Logs**: [`results/raw/`](file:///d:/New%20folder/cognodb-benchmark/results/raw/) (Every run preserved with unique run ID)
- **Compliance & Security Reports**: [`reports/`](file:///d:/New%20folder/cognodb-benchmark/reports/)
  - Security Audit: `final_security_audit.md` (`SAFE TO PUBLISH`)
  - Wexa Compliance: `final_assignment_compliance.md` (`PASS`)
- **Publication PDF Report**: [`Comparative_Graph_Database_Benchmark_Report.pdf`](file:///d:/New%20folder/cognodb-benchmark/Comparative_Graph_Database_Benchmark_Report.pdf)

---

## Reproducibility

- **Canonical Dataset**: Normalized into deterministic `nodes.csv` and `relationships.csv`.
- **Dataset Integrity**: Verified via SHA-256 hashes (`Nodes: 713f082a...`, `Relationships: ba160b3d...`).
- **State Integrity**: 100% node and relationship count verification before and after write workloads.
- **Timing Accuracy**: Monotonic high-resolution nanosecond timing using `time.perf_counter()`.
- **Warm-Up Protocol**: 10 non-measured warm-up iterations executed prior to recorded runs.

---

## Security

- Zero hardcoded passwords, tokens, API keys, or authenticated connection strings in source code.
- `.env` is listed in `.gitignore` and ignored by Git.
- Benchmark outputs log standard runtime metadata only and exclude connection secrets.
- Full security audit verified repository safety for public publication (`SAFE TO PUBLISH`).

---

## Limitations

1. **Deployment Architecture**: CognoDB Cloud was accessed over a remote WAN network, whereas comparison databases ran locally via Docker containers over loopback sockets.
2. **Single Dataset Scope**: Evaluation conducted on the SNAP Wiki-Vote graph (7,115 nodes, 103,689 relationships).
3. **Neo4j RAM Requirement**: Neo4j required 768 MB RAM minimum to prevent JVM startup memory failure, while C/C++ engines operated at 256 MB RAM.
4. **FalkorDB Concurrency Trajectory**: FalkorDB throughput peaked at c=4 (3,724.85 ops/sec) and declined at higher tested concurrency levels; the benchmark does not establish the underlying cause.

---

## Assignment Information
This project was developed for the **Wexa AI Take-Home Benchmark Assignment 1**.

---

## Final Report
Reviewers are encouraged to inspect the complete, 7-page publication PDF report:

📄 **[`Comparative_Graph_Database_Benchmark_Report.pdf`](file:///d:/New%20folder/cognodb-benchmark/Comparative_Graph_Database_Benchmark_Report.pdf)** (SHA-256: `9293f8e43b8ece7b06a8be4d4724a4c1a25fc8eb56b4bd078be535b2b2598b5f`)