"""Build the HW6 evidence report from checked-in raw results."""

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "Parab_HW6.pdf"
RAW = Path(__file__).resolve().parent / "raw"

def current_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "refs/tags/hw6^{}"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unverified"

def main():
    styles = getSampleStyleSheet()
    title = ParagraphStyle("TitleHW6", parent=styles["Title"], fontSize=20, leading=25, alignment=TA_CENTER, spaceAfter=16)
    heading = ParagraphStyle("HeadingHW6", parent=styles["Heading1"], fontSize=14, leading=18, spaceBefore=10, spaceAfter=8)
    subheading = ParagraphStyle("SubheadingHW6", parent=styles["Heading2"], fontSize=12, leading=15, spaceBefore=8, spaceAfter=5)
    body = ParagraphStyle("BodyHW6", parent=styles["BodyText"], fontSize=11, leading=15, spaceAfter=7)
    small = ParagraphStyle("SmallHW6", parent=body, fontSize=9, leading=12)
    commit = current_commit()
    story = [Paragraph("DATA 260 - Agentic AI<br/>Homework 6 - Evidence Report", title),
             Paragraph(f"Student Name: Shoury Parab<br/>SID4: 7085<br/>Repository: data260-7085<br/>Branch: hw6<br/>Tagged commit: {commit}<br/>Hardware: Intel Core i5-6200U @ 2.30GHz<br/>Configuration: PORT_BASE=8785, PREFIX=s7085, SEED=7085, VERIFY_SEED=267085, DOMAIN_ID=5<br/>Local model: Ollama llama3.2:3b<br/>Repository: https://github.com/shoddy16/data260-7085", body), Spacer(1, 10)]
    story += [Paragraph("Submission status", heading), Paragraph("This report was generated from the current HW6 branch and checked-in machine-readable results. FastAPI, PyMongo, and Ollama dependencies are installed and the API validation smoke checks pass. Docker Desktop's MongoDB engine is unavailable, so live MongoDB collection evidence and dependent screenshots are not claimed.", body)]
    story += [Paragraph("Part 1 - MongoDB Document API", heading), Paragraph("The implementation adds a MongoDB-backed document view at /api/documents with required short text, optional description, constrained status/category fields, an inspection datetime, automatic timestamps, Pydantic validation, and MongoDB JSON Schema validation. CRUD handlers return explicit validation, not-found, database, and success status codes.", body), Paragraph("Relevant implementation: hw6_mongo.py, hw6_memory.py, routers/hw6.py, and main.py. Live MongoDB screenshots remain pending because MongoDB and PyMongo were unavailable in this run.", small)]
    story += [Paragraph("Part 2 - Short-, Long-, and Episodic Memory", heading), Paragraph("The /api/chat, /api/memory/{user_id}, and /api/aggregate/{user_id} routes use messages, summaries, and episodes. Chat turns save user and assistant messages, assemble system/session/lifetime/short-term/episodic context, create deterministic local embeddings, retrieve episodes by cosine similarity, and trigger summaries every configured number of user messages.", body), Paragraph("Offline deterministic tests and FastAPI route validation pass. A live Ollama session was attempted, but the ten-turn memory run exceeded the bounded execution window; MongoDB Compass, persisted collection, memory JSON, aggregate JSON, and screenshot evidence remain blocked by the unavailable MongoDB service.", small)]
    story += [Paragraph("Part 3 - What Memory Costs", heading)]
    metrics = json.loads((RAW / "memory_cost_summary.json").read_text(encoding="utf-8"))
    rows = [["Setting", "Mean prompt tokens/turn", "Mean latency (ms)", "Probe quality"]]
    for item in metrics["settings"]:
        rows.append([item["setting"], str(item["mean_prompt_tokens_per_turn"]), str(item["mean_latency_ms"]), f"{item['probe_quality']}/5"])
    table = Table(rows, colWidths=[2.0*inch, 1.6*inch, 1.35*inch, 1.25*inch])
    table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#d9eaf7")), ("GRID", (0,0), (-1,-1), 0.5, colors.grey), ("FONTSIZE", (0,0), (-1,-1), 9), ("VALIGN", (0,0), (-1,-1), "TOP")]))
    story += [table, Spacer(1, 8), Paragraph(f"The 30-turn deterministic sweep selected {metrics['best_setting']} as the best measured token-cost setting and {metrics['worst_setting']} as the worst. Estimated cost for 10,000 conversations was ${metrics['cost_10000_conversations_best_usd']} best and ${metrics['cost_10000_conversations_worst_usd']} worst using the required input/output prices.", body), Paragraph("Raw records: reports/hw06/raw/memory_token_records.csv, memory_cost_comparison.json, memory_cost_summary.json. Probe definitions: memory_probes.yaml.", small)]
    story += [Paragraph("Part 4 - File-Based Memory and Consolidation", heading), Paragraph("AGENT.md now contains project, technology, coding, testing, and prohibited-action instructions. MEMORY.md stores durable facts and includes a timestamp. The /memory, /compact, /dream, and /help commands are implemented in file_memory.py. The original contradictory 55-line fixture is preserved in reports/hw06/raw/MEMORY_original.md.", body), Paragraph("The actual consolidation reduced the original fixture to 32 nonblank/noncomment facts, merged duplicates, and explicitly recorded the MySQL/MongoDB contradiction for review. Deterministic tests verify command output and contradiction handling.", body), Paragraph("MongoDB-backed memory is queryable and scalable across sessions but depends on a running database and is less directly inspectable as plain text. File-based memory is highly inspectable and restart-persistent, but it requires consolidation and becomes less scalable across many sessions. MongoDB is better for searchable episodic facts; a curated MEMORY.md is better for facts that must remain visible and hard to forget.", body)]
    story += [Paragraph("Verification and AI Use", heading), Paragraph("Verification output is written by verify_hw6.py to reports/hw06/verification.json. AI_USE.md documents the assistant’s role, independent verification, detected problems, and corrective changes. RUN_LOG.txt records the implementation and experiment commands.", body), Paragraph("Required final GitHub push/tag and live-service screenshots are not reported as complete until the missing dependency installation and service checks succeed.", body)]
    doc = SimpleDocTemplate(str(OUT), pagesize=letter, rightMargin=.7*inch, leftMargin=.7*inch, topMargin=.65*inch, bottomMargin=.65*inch)
    doc.build(story)
    print(f"Created {OUT} ({OUT.stat().st_size} bytes)")

if __name__ == "__main__": main()
