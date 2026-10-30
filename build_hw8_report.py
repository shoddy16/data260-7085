from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "reports" / "hw08" / "Parab_HW8.pdf"


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=14, leading=17, spaceAfter=8, fontName="Helvetica-Bold")
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12, leading=15, spaceAfter=6, fontName="Helvetica-Bold")
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=11, leading=14, spaceAfter=6)
    small = ParagraphStyle("Small", parent=body, fontSize=9, leading=11)
    doc = SimpleDocTemplate(str(OUT), pagesize=letter, rightMargin=.6*inch, leftMargin=.6*inch, topMargin=.55*inch, bottomMargin=.55*inch)
    story = [Paragraph("DATA 260 Homework 8 - Kafka Restaurant Inspection Service", h1), Paragraph("Shoury Parab | SID4 7085 | Repository: https://github.com/shoddy16/data260-7085", body), Paragraph("Configuration: PORT_BASE=8085, PREFIX=s7085, SEED=7085, VERIFY_SEED=267085, DOMAIN_ID=5. Hardware/model: as documented in HW7; local model llama3.2:3b. Final commit/tag is recorded in verification.json after packaging.", body), Spacer(1, 6)]
    story += [Paragraph("Section 0 - Scope and evidence", h1), Paragraph("This report extends the restaurant-inspection application from HW7. The implementation includes an aiokafka runtime plus deterministic offline tests. Live Docker/Kafka evidence is only claimed when the command actually ran; offline evidence is labeled as such.", body)]
    story += [Paragraph("Part 1 - Request/response service", h1), Paragraph("Topics: s7085_entity_requests and s7085_entity_responses. Requests contain correlation_id, reply_to, operation, and data. CREATE_ENTITY validates restaurant inspection fields, generates a UUID, and stores the record in the worker dictionary. GET_ENTITY returns the record or a clean not-found error. Correlation IDs are echoed on all responses.", body), Paragraph("Relevant code: kafka_protocol.py, kafka_runtime.py, kafka_rpc.py, routers/hw8.py, homework_demo.py.", small)]
    story += [Paragraph("Part 2 - Three-agent pipeline", h1), Paragraph("Planner, Writer, and Reviewer are separate entry points. The real runtime uses Kafka consumer/producer stages and manual offset commits. The deterministic pipeline records the same four-topic journey for repeatable smoke tests: s7085_inbox -> s7085_tasks -> s7085_drafts -> s7085_final.", body)]
    story += [Paragraph("Part 3 - Failure behavior and ordering", h1)]
    data = [["Scenario", "Before", "After"], ["Duplicate", "Replay could repeat side effect", "correlation-id cache returns the original response"], ["Consumer death", "uncommitted work can redeliver", "commit occurs after successful publish"], ["Poison", "bad message can block", "bounded retries publish s7085_dead_letter"], ["Ordering", "two partitions may interleave", "entity key keeps related records in one partition"]]
    t = Table(data, colWidths=[1.15*inch, 2.3*inch, 2.9*inch]); t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#d9eaf7")), ("GRID", (0,0), (-1,-1), .4, colors.grey), ("VALIGN", (0,0), (-1,-1), "TOP"), ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("FONTSIZE", (0,0), (-1,-1), 9)])); story += [t, Spacer(1, 8), Paragraph("The raw artifact part3_failure_ordering.json records VERIFY_SEED=267085, 20 messages, duplicate idempotency, consumer restart/commit semantics, retry count, and dead-letter result. Kafka provides decoupling and independent scaling; it adds responsibilities for idempotency, retries, offsets, and partition-key ordering.", body)]
    story += [Paragraph("Verification and limitations", h1), Paragraph("Run python verify_hw8.py to write reports/hw08/verification.json. The test suite covers validation, correlation preservation, UUID round trips, duplicate delivery, pipeline output, dead-letter configuration, and keyed ordering. Live Docker/Kafka execution, JMeter benchmarking, and collaborator-permission verification remain environment/account checks unless their logs are present in RUN_LOG.txt.", body)]
    story += [Paragraph("AI_USE", h1), Paragraph("AI assistance was used for scaffolding, review, and report formatting. I selected the restaurant domain, supplied configuration, inspected the outputs, and verified tests. I independently checked correlation preservation and the commit/tag sequencing. Changes were retained only when the source, deterministic tests, and artifacts agreed.", body)]
    doc.build(story)


if __name__ == "__main__":
    build()
