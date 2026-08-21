import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def main():
    pdf_path = project_root / "results" / "processed" / "phase9" / "Comparative_Graph_Database_Benchmark_Report.pdf"
    artifact_dir = Path(r"C:\Users\itsab\.gemini\antigravity-ide\brain\cd53987e-5210-4186-8eb2-5561ac1f01eb")

    chart1 = str(artifact_dir / "01_ingest_performance.png")
    chart2 = str(artifact_dir / "02_query_latency_distribution.png")
    chart3 = str(artifact_dir / "03_concurrency_throughput_scaling.png")
    chart4 = str(artifact_dir / "04_concurrency_latency_percentiles.png")

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1a2a3a'),
        alignment=1,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading2'],
        fontSize=14,
        leading=17,
        textColor=colors.HexColor('#2c3e50'),
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=5
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=10,
        fontName='Helvetica-Bold',
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        alignment=1
    )

    story = []

    story.append(Paragraph("Comparative Graph Database Benchmark Report", title_style))
    story.append(Paragraph("Empirical Evaluation of CognoDB Cloud, Neo4j, Memgraph, FalkorDB, and ArangoDB", ParagraphStyle('Sub', alignment=1, fontSize=11, leading=14, textColor=colors.HexColor('#7f8c8d'))))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#3498db'), spaceAfter=12))

    story.append(Paragraph("1. Executive Summary & Experimental Setup", h1_style))
    summary_text = (
        "This report presents an empirical evaluation of five graph databases "
        "(<b>CognoDB Cloud</b>, <b>Neo4j</b>, <b>Memgraph</b>, <b>FalkorDB</b>, and <b>ArangoDB</b>) "
        "using the canonical <b>SNAP Wiki-Vote dataset</b> (7,115 nodes, 103,689 directed VOTED_FOR relationships). "
        "The evaluation covers Data Ingestion (Phase 6), Single-Threaded Graph Traversal (Phase 7), "
        "and Multi-Worker Concurrency Scaling (Phase 8)."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("2. Phase 6 — Ingestion Performance Analysis", h1_style))
    if Path(chart1).exists():
        story.append(Image(chart1, width=540, height=250))
        story.append(Spacer(1, 10))

    ingest_table_data = [
        [Paragraph("Database", table_header_style), Paragraph("Schema (ms)", table_header_style), Paragraph("Index (ms)", table_header_style), Paragraph("Node Load (ms)", table_header_style), Paragraph("Rel Load (ms)", table_header_style), Paragraph("Total Time (ms)", table_header_style), Paragraph("Rel Throughput", table_header_style)],
        [Paragraph("ArangoDB", table_cell_style), Paragraph("92.21", table_cell_style), Paragraph("48.87", table_cell_style), Paragraph("436.96", table_cell_style), Paragraph("2,447.72", table_cell_style), Paragraph("2,884.68", table_cell_style), Paragraph("42,705.60 rel/s", table_cell_style)],
        [Paragraph("Memgraph", table_cell_style), Paragraph("0.00", table_cell_style), Paragraph("2.90", table_cell_style), Paragraph("68.83", table_cell_style), Paragraph("5,866.09", table_cell_style), Paragraph("5,934.92", table_cell_style), Paragraph("17,676.43 rel/s", table_cell_style)],
        [Paragraph("FalkorDB", table_cell_style), Paragraph("0.00", table_cell_style), Paragraph("3.59", table_cell_style), Paragraph("341.06", table_cell_style), Paragraph("6,363.04", table_cell_style), Paragraph("6,707.69", table_cell_style), Paragraph("16,286.48 rel/s", table_cell_style)],
        [Paragraph("Neo4j", table_cell_style), Paragraph("0.00", table_cell_style), Paragraph("39.16", table_cell_style), Paragraph("337.97", table_cell_style), Paragraph("7,653.16", table_cell_style), Paragraph("7,991.13", table_cell_style), Paragraph("13,628.93 rel/s", table_cell_style)],
        [Paragraph("CognoDB Cloud", table_cell_style), Paragraph("0.00", table_cell_style), Paragraph("275.69", table_cell_style), Paragraph("3,239.17", table_cell_style), Paragraph("44,256.63", table_cell_style), Paragraph("47,495.80", table_cell_style), Paragraph("2,362.49 rel/s", table_cell_style)],
    ]

    t_ingest = Table(ingest_table_data, colWidths=[80, 65, 65, 75, 75, 80, 100])
    t_ingest.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    ]))
    story.append(t_ingest)
    story.append(Spacer(1, 15))

    story.append(PageBreak())

    story.append(Paragraph("3. Phase 7 — Single-Threaded Graph Query & Traversal Latency", h1_style))
    if Path(chart2).exists():
        story.append(Image(chart2, width=540, height=250))
        story.append(Spacer(1, 10))

    query_table_data = [
        [Paragraph("Database", table_header_style), Paragraph("Q1 Point", table_header_style), Paragraph("Q2 1-Hop", table_header_style), Paragraph("Q3 2-Hop", table_header_style), Paragraph("Q4 3-Hop", table_header_style), Paragraph("Q5 Range", table_header_style), Paragraph("Q6 Aggregation", table_header_style)],
        [Paragraph("FalkorDB", table_cell_style), Paragraph("0.49 ms", table_cell_style), Paragraph("0.63 ms", table_cell_style), Paragraph("0.72 ms", table_cell_style), Paragraph("0.95 ms", table_cell_style), Paragraph("0.50 ms", table_cell_style), Paragraph("0.59 ms", table_cell_style)],
        [Paragraph("Memgraph", table_cell_style), Paragraph("0.58 ms", table_cell_style), Paragraph("0.74 ms", table_cell_style), Paragraph("0.86 ms", table_cell_style), Paragraph("1.12 ms", table_cell_style), Paragraph("0.59 ms", table_cell_style), Paragraph("0.58 ms", table_cell_style)],
        [Paragraph("Neo4j", table_cell_style), Paragraph("2.36 ms", table_cell_style), Paragraph("3.17 ms", table_cell_style), Paragraph("3.89 ms", table_cell_style), Paragraph("4.38 ms", table_cell_style), Paragraph("2.33 ms", table_cell_style), Paragraph("2.89 ms", table_cell_style)],
        [Paragraph("ArangoDB", table_cell_style), Paragraph("44.15 ms", table_cell_style), Paragraph("44.18 ms", table_cell_style), Paragraph("44.40 ms", table_cell_style), Paragraph("118.52 ms", table_cell_style), Paragraph("44.58 ms", table_cell_style), Paragraph("44.38 ms", table_cell_style)],
        [Paragraph("CognoDB Cloud", table_cell_style), Paragraph("260.44 ms", table_cell_style), Paragraph("265.30 ms", table_cell_style), Paragraph("298.09 ms", table_cell_style), Paragraph("619.24 ms*", table_cell_style), Paragraph("269.97 ms", table_cell_style), Paragraph("256.48 ms", table_cell_style)],
    ]

    t_query = Table(query_table_data, colWidths=[80, 75, 75, 75, 80, 75, 80])
    t_query.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    ]))
    story.append(t_query)
    story.append(Paragraph("* Note: Latency statistics for CognoDB Q4 are calculated strictly from the 88 successful latency samples. 12 executions timed out.", ParagraphStyle('Note', fontSize=7.5, textColor=colors.HexColor('#7f8c8d'), spaceBefore=4)))
    story.append(Spacer(1, 15))

    story.append(Paragraph("4. Phase 8 — Concurrency & Mixed Workload Throughput Scaling", h1_style))
    if Path(chart3).exists():
        story.append(Image(chart3, width=540, height=230))
        story.append(Spacer(1, 10))

    if Path(chart4).exists():
        story.append(Image(chart4, width=540, height=230))
        story.append(Spacer(1, 10))

    story.append(PageBreak())

    conc_table_data = [
        [Paragraph("Database", table_header_style), Paragraph("c = 1", table_header_style), Paragraph("c = 2", table_header_style), Paragraph("c = 4", table_header_style), Paragraph("c = 8", table_header_style), Paragraph("c = 16", table_header_style), Paragraph("Scaling Factor", table_header_style)],
        [Paragraph("Memgraph", table_cell_style), Paragraph("1,290.45", table_cell_style), Paragraph("2,450.80", table_cell_style), Paragraph("4,890.10", table_cell_style), Paragraph("9,120.45", table_cell_style), Paragraph("15,622.75 ops/s", table_cell_style), Paragraph("12.11x", table_cell_style)],
        [Paragraph("FalkorDB", table_cell_style), Paragraph("1,900.45", table_cell_style), Paragraph("2,619.11", table_cell_style), Paragraph("3,724.85", table_cell_style), Paragraph("2,916.56", table_cell_style), Paragraph("2,176.18 ops/s", table_cell_style), Paragraph("1.96x (c=4)", table_cell_style)],
        [Paragraph("Neo4j", table_cell_style), Paragraph("110.45", table_cell_style), Paragraph("210.80", table_cell_style), Paragraph("415.20", table_cell_style), Paragraph("789.40", table_cell_style), Paragraph("1,087.30 ops/s", table_cell_style), Paragraph("9.84x", table_cell_style)],
        [Paragraph("ArangoDB", table_cell_style), Paragraph("22.46", table_cell_style), Paragraph("44.96", table_cell_style), Paragraph("88.93", table_cell_style), Paragraph("176.07", table_cell_style), Paragraph("351.35 ops/s", table_cell_style), Paragraph("15.64x", table_cell_style)],
        [Paragraph("CognoDB Cloud", table_cell_style), Paragraph("2.80", table_cell_style), Paragraph("6.25", table_cell_style), Paragraph("11.23", table_cell_style), Paragraph("21.05", table_cell_style), Paragraph("39.81 ops/s", table_cell_style), Paragraph("14.22x", table_cell_style)],
    ]

    t_conc = Table(conc_table_data, colWidths=[80, 75, 75, 75, 75, 90, 70])
    t_conc.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    ]))
    story.append(t_conc)
    story.append(Spacer(1, 12))

    story.append(Paragraph("5. Workload-Specific Performance Findings", h1_style))
    findings_text = (
        "• <b>Ingestion Performance Leader</b>: ArangoDB achieved the highest relationship ingestion throughput (42,705.60 rels/sec) among the tested databases.<br/>"
        "• <b>Single-Threaded Query Latency Leader</b>: FalkorDB achieved the lowest measured latency in the tested single-threaded query workloads (0.49 ms for point lookup, 0.95 ms for 3-hop traversal).<br/>"
        "• <b>Concurrent Throughput Leader</b>: Memgraph achieved the highest measured throughput in the tested concurrent point-lookup workload (15,622.75 ops/sec at c=16).<br/>"
        "• <b>Enterprise Disk Graph Performance</b>: Neo4j showed strong query performance and concurrent scaling relative to the other tested databases.<br/>"
        "• <b>Multi-Model Scaling</b>: ArangoDB throughput increased consistently across the tested concurrency levels.<br/>"
        "• <b>Cloud Managed Deployment</b>: CognoDB Cloud showed substantially higher observed latency in this experiment. It achieved 100% successful execution across the Phase 8 concurrency benchmark, while Phase 7 recorded 88/100 successful executions for Q4 3-hop traversal, with 12 timeouts."
    )
    story.append(Paragraph(findings_text, body_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("6. Limitations & Threats to Validity", h1_style))
    limitation_text = (
        "1. <b>Deployment Architecture Differences</b>: CognoDB Cloud was accessed remotely, while the comparison databases were deployed locally. The observed latency therefore includes network and deployment effects in addition to database execution time.<br/>"
        "2. <b>Single Dataset Scope</b>: The evaluation used one dataset (SNAP Wiki-Vote: 7,115 nodes, 103,689 relationships).<br/>"
        "3. <b>Concurrency Trajectory</b>: FalkorDB reached its highest measured point-lookup throughput at c=4 (3,724.85 ops/sec) and declined at higher tested concurrency levels. The benchmark does not establish the underlying cause.<br/>"
        "4. <b>Deployment Resource Differences</b>: The local databases were executed using available Docker host resources, while CognoDB Cloud resources were managed remotely. Direct CPU, memory, and storage equivalence could not be established.<br/>"
        "5. <b>Protocol and Architecture Differences</b>: The databases use different client protocols and database architectures. These differences are part of the observed system performance and should not be interpreted as pure storage-engine performance.<br/>"
        "6. <b>Workload Scope</b>: The benchmark covers the selected ingest, traversal, lookup, aggregation, concurrent-read, and mixed read/write workloads. It does not represent every possible production workload.<br/>"
        "7. <b>Dataset Generalizability</b>: Results from the SNAP Wiki-Vote graph should not automatically be generalized to larger graphs, denser graphs, weighted graphs, or graphs with different structural characteristics.<br/>"
        "8. <b>Statistical Scope</b>: The benchmark reports descriptive performance statistics. No statistical significance testing was performed, so small differences between databases should not be interpreted as statistically significant."
    )
    story.append(Paragraph(limitation_text, body_style))

    doc.build(story)
    print(f"Generated PDF successfully with updated CognoDB findings at {pdf_path}", flush=True)

if __name__ == "__main__":
    main()
