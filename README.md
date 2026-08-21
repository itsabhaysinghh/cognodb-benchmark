# Comparative Graph Database Benchmark Framework

A comprehensive, reproducible performance benchmarking framework comparing five graph databases (**CognoDB Cloud**, **Neo4j**, **Memgraph**, **FalkorDB**, and **ArangoDB**) using the canonical **SNAP Wiki-Vote** dataset.

---

## 1. Project Purpose
The purpose of this framework is to provide a fair, transparent, and reproducible comparative benchmark evaluating data ingestion throughput, single-threaded graph query and traversal latencies, and multi-worker concurrent throughput scaling across diverse graph database engines.

---

## 2. Benchmark Scope
The benchmark spans three evaluation phases:
- **Phase 6 — Data Ingestion**: Bulk loading speed of nodes and relationships across 3 clean independent runs per database.
- **Phase 7 — Graph Query & Traversal**: Single-threaded execution of 6 workloads (`Q1_POINT_LOOKUP`, `Q2_1HOP_TRAVERSAL`, `Q3_2HOP_TRAVERSAL`, `Q4_3HOP_TRAVERSAL`, `Q5_FILTERED_LOOKUP`, `Q6_AGGREGATION`) across 100 measured queries + 10 warm-ups per workload.
- **Phase 8 — Concurrency & Scaling**: Multi-threaded execution across 4 workloads (`CONCURRENT_POINT_LOOKUP`, `CONCURRENT_1HOP`, `MIXED_READ`, `MIXED_READ_WRITE`) and 5 concurrency levels (`c=1, 2, 4, 8, 16`) using persistent connection pools.

---

## 3. Dataset
The canonical dataset is derived from the **SNAP Wiki-Vote** network:
- **Nodes**: `7,115` (`User` vertices)
- **Relationships**: `103,689` (`VOTED_FOR` directed edges)
- **Canonical Files**:
  - `data/processed/nodes.csv`
  - `data/processed/relationships.csv`
  - `data/processed/dataset_manifest.json`

---

## 4. Database Systems Tested
1. **CognoDB Cloud**: Remote managed cloud graph database (Cypher / Bolt TLS).
2. **Neo4j**: 5.26.0 Community Edition (Cypher / Bolt TCP).
3. **Memgraph**: Community Edition (Cypher / Bolt TCP).
4. **FalkorDB**: v4.20.2 Community Edition (Cypher / Falkor Redis Protocol).
5. **ArangoDB**: 3.12.3 Community Edition (AQL / HTTP REST).

---

## 5. Architecture
```
cognodb-benchmark/
├── benchmark/
│   ├── timing.py
│   ├── validation.py
│   ├── ingest.py
│   ├── query_workloads.py
│   ├── query_engine.py
│   ├── concurrent_workloads.py
│   └── concurrent_engine.py
├── config/
│   └── fairness_record.yaml
├── data/
│   ├── raw/
│   └── processed/
├── databases/
│   ├── base.py
│   ├── cognodb.py
│   ├── neo4j.py
│   ├── memgraph.py
│   ├── falkordb.py
│   └── arangodb.py
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── reports/
│   ├── phase10_release_audit.md
│   └── phase10_release_audit.json
├── results/
│   ├── raw/
│   └── processed/
└── scripts/
```

---

## 6. Installation

Clone the repository and set up a Python 3.12 virtual environment:

```bash
git clone <repository-url>
cd cognodb-benchmark
python -m venv .venv
```

Activate virtual environment:
- Windows (PowerShell):
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- Linux / macOS:
  ```bash
  source .venv/bin/activate
  ```

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## 7. Environment Configuration

Copy `.env.example` to `.env` and fill in connection details:

```bash
cp .env.example .env
```

Example `.env` configuration:
```env
COGNODB_URI=bolt+s://your-cognodb-host
COGNODB_USERNAME=cognodb
COGNODB_PASSWORD=your_cloud_password

NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=local_dev_password

MEMGRAPH_URI=bolt://localhost:7688
MEMGRAPH_USERNAME=
MEMGRAPH_PASSWORD=

FALKORDB_URI=falkor://localhost:6379
FALKORDB_USERNAME=
FALKORDB_PASSWORD=

ARANGODB_URI=http://localhost:8529
ARANGODB_USERNAME=root
ARANGODB_PASSWORD=local_dev_password
ARANGODB_DATABASE=_system
```

---

## 8. Docker Setup

Start local database containers:

```bash
docker compose up -d
```

Verify container status:
```bash
docker compose ps
```

---

## 9. Dataset Validation

Validate the SHA-256 hash and manifest of the canonical dataset:

```bash
python -c "from benchmark.validation import DatasetValidator; from pathlib import Path; v=DatasetValidator(Path('.')); print(v.validate())"
```

---

## 10. Dataset Normalization

To re-process raw SNAP data into canonical CSV format:

```bash
python scripts/normalize_dataset.py
```

---

## 11. Database Connection Verification

Test reachability across all database environments:

```bash
python scripts/check_database_environments.py
```

---

## 12. Phase 6 Benchmark Execution (Ingestion)

Run 15 clean ingestion runs across all 5 databases:

```bash
python scripts/run_full_benchmark.py
```

Results are saved to `results/processed/ingest_benchmark_summary.json`.

---

## 13. Phase 7 Benchmark Execution (Query Latency)

Run the single-threaded 6-workload query benchmark:

```bash
python scripts/run_final_query_benchmark.py
```

Results are saved to `results/processed/query_benchmark_final_summary.json`.

---

## 14. Phase 8 Benchmark Execution (Concurrency)

Run the multi-threaded concurrency scaling benchmark across 5 databases × 4 workloads × 5 concurrency levels (`c=1..16`):

```bash
python scripts/run_full_phase8_benchmark.py
```

Results are saved to `results/processed/phase8/concurrency_benchmark_final_summary.json`.

---

## 15. Phase 9 Report Generation

Generate high-resolution PNG charts and compile the final benchmark markdown and PDF reports:

```bash
python scripts/generate_phase9_charts.py
python scripts/generate_audited_final_report.py
python scripts/generate_walkthrough_pdf.py
```

Outputs:
- Charts: `results/processed/phase9/charts/`
- Markdown Report: `results/processed/phase9/final_benchmark_report.md`
- PDF Publication Report: `results/processed/phase9/Comparative_Graph_Database_Benchmark_Report.pdf`

---

## 16. Result Locations
- Raw Run Data: `results/raw/`
- Phase 6 Summary: `results/processed/ingest_benchmark_summary.json`
- Phase 7 Summary: `results/processed/query_benchmark_final_summary.json`
- Phase 8 Summary: `results/processed/phase8/concurrency_benchmark_final_summary.json`
- Phase 9 Reports: `results/processed/phase9/`

---

## 17. Reproducibility Instructions
To completely reproduce the full benchmark suite end-to-end:

```bash
# 1. Environment & Docker
pip install -r requirements.txt
docker compose up -d

# 2. Connection & Dataset Verification
python scripts/check_database_environments.py

# 3. Benchmark Execution
python scripts/run_full_benchmark.py
python scripts/run_final_query_benchmark.py
python scripts/run_full_phase8_benchmark.py

# 4. Analysis & PDF Generation
python scripts/generate_phase9_charts.py
python scripts/generate_audited_final_report.py
python scripts/generate_walkthrough_pdf.py
```

---

## 18. Security Notes
- Never commit `.env` files containing real production passwords.
- `.env` is ignored in `.gitignore`.
- Benchmark scripts and result files never store or log passwords or tokens.

---

## 19. Limitations
1. **Deployment Architecture Differences**: Remote Cloud WAN vs Local Docker loopback sockets.
2. **Single Dataset Scope**: SNAP Wiki-Vote network (7,115 nodes, 103,689 relationships).
3. **Hardware & Resource Allocation**: Docker container host resources vs managed cloud instance resources.
4. **Descriptive Statistics**: Reports empirical descriptive metrics without inferential statistical hypothesis testing.

---

## 20. Citation & Reference Information
- Dataset Source: Stanford Network Analysis Project (SNAP) — Wiki-Vote network dataset.
- Cypher Query Language: OpenCypher Standards.
- ArangoDB Query Language: ArangoDB AQL Documentation.