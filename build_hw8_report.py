"""Build a detailed HW8 report from current source and evidence."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Table, TableStyle

ROOT = Path(__file__).resolve().parent
REPORT_DIR = ROOT / "reports" / "hw08"
OUT = REPORT_DIR / "Parab_HW8.pdf"


def source(path: str, start: int, end: int) -> str:
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    return "\n".join(f"{i + 1:>3} {lines[i]}" for i in range(start - 1, min(end, len(lines))))


def build() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    cover = ParagraphStyle("Cover", parent=styles["Title"], fontSize=20, leading=25, alignment=TA_CENTER, spaceAfter=18)
    h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"], fontSize=14, leading=18, fontName="Helvetica-Bold", spaceAfter=8
    )
    h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"], fontSize=12, leading=15, fontName="Helvetica-Bold", spaceBefore=5, spaceAfter=5
    )
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=11, leading=14, spaceAfter=7)
    caption = ParagraphStyle("Caption", parent=body, fontSize=9, leading=11, textColor=colors.HexColor("#444444"))
    code = ParagraphStyle(
        "Code",
        parent=body,
        fontName="Courier",
        fontSize=7.3,
        leading=9,
        leftIndent=5,
        rightIndent=5,
        backColor=colors.HexColor("#f3f5f7"),
    )
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        rightMargin=0.58 * inch,
        leftMargin=0.58 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )
    story: list = []

    story += [
        Paragraph("DATA 260 Homework 8", cover),
        Paragraph("Kafka Request/Response and Multi-Agent Restaurant Inspection Pipeline", h1),
        Paragraph(
            "Student: Shoury Parab<br/>SID4: 7085<br/>Repository: https://github.com/shoddy16/data260-7085", body
        ),
        Paragraph(
            "Configuration: SID4=7085 | PORT_BASE=8085 | PREFIX=s7085 | SEED=7085 | VERIFY_SEED=267085 | DOMAIN_ID=5<br/>Assigned domain: local restaurant inspections.<br/>Python: 3.12.10. Local model: llama3.2:3b.<br/>Published hw8 tag currently points to 1b843e76d268dd9076230411e098e96ed43b9a8f. The completion branch is intentionally not retagged until approval and live-evidence review.",
            body,
        ),
        Paragraph(
            "Hardware verification: Windows hardware queries returned Access denied in this environment, so no hardware specification is claimed.",
            body,
        ),
        Paragraph("Evidence classification", h2),
        Paragraph(
            "[UNIT/OFFLINE] means a deterministic test or in-process model. [LIVE] is reserved for actual Kafka/Docker execution. The current environment could not connect to the Docker Desktop engine; therefore no live Kafka result or screenshot is represented as successful.",
            body,
        ),
        PageBreak(),
    ]

    story += [
        Paragraph("1. Executive summary and architecture", h1),
        Paragraph(
            "This HW8 implementation extends the HW7 restaurant-inspection repository. The request/response path has a FastAPI wrapper, two exact RPC topics, an aiokafka worker, correlation-preserving envelopes, UUID entity IDs, dictionary storage, validation, and manual offset commits. The agent path has four required topics and separate Planner, Writer, Reviewer entry points. Offline tests provide objective coverage while clearly separating those checks from unavailable Docker/Kafka evidence.",
            body,
        ),
        Paragraph(
            "Architecture: FastAPI -> s7085_entity_requests -> EntityWorker -> reply_to/s7085_entity_responses. The agent flow is send_question -> s7085_inbox -> planner -> s7085_tasks (2 partitions) -> writer -> s7085_drafts -> reviewer -> s7085_final.",
            body,
        ),
        Paragraph("Relevant implementation files", h2),
        Preformatted(
            "hw8_config.py\nkafka_protocol.py\nkafka_rpc.py\nkafka_runtime.py\nhomework_demo.py\nplanner.py / writer.py / reviewer.py / send_question.py\nfailure_ordering.py\nverify_hw8.py\ntests/test_hw8.py",
            code,
        ),
        PageBreak(),
    ]

    story += [
        Paragraph("2. Part 1 - Kafka request/response", h1),
        Paragraph("Objective and rubric requirement", h2),
        Paragraph(
            "Use exactly two PREFIX-prefixed RPC topics, preserve the request envelope and correlation ID, implement CREATE_ENTITY and GET_ENTITY for the restaurant-inspection domain, return clean validation errors, and demonstrate the full sequence.",
            body,
        ),
        Paragraph("Implementation", h2),
        Paragraph(
            "EntityWorker.process validates the envelope and restaurant fields, generates a UUID, stores the entity in a worker-side dictionary, and caches responses by correlation ID. The real runtime consumes s7085_entity_requests, publishes to reply_to, and commits only after publication.",
            body,
        ),
        Paragraph("Actual code snippet: kafka_protocol.py / EntityWorker.process", h2),
        Preformatted(source("kafka_protocol.py", 35, 75), code),
        Paragraph("Code explanation", h2),
        Paragraph(
            "The required fields are restaurantName, location, email, description, and category; score is bounded to 0-100 when present. Every response includes correlation_id. The request/response wrapper adds the two topic names to its result, and HW8_LIVE_KAFKA=1 selects the aiokafka path.",
            body,
        ),
        Paragraph("Runtime evidence", h2),
        Paragraph(
            "[LIVE SCREENSHOT MISSING] Docker Desktop was not running: docker reported that the dockerDesktopLinuxEngine named pipe was unavailable. Consequently the required docker ps, worker readiness, FastAPI startup, and real CREATE -> GET screenshots remain unverified. The offline test and homework_demo output are not substituted for live Kafka evidence.",
            caption,
        ),
        PageBreak(),
    ]

    story += [
        Paragraph("3. Part 2 - Planner, Writer, Reviewer", h1),
        Paragraph("Objective and rubric requirement", h2),
        Paragraph(
            "Run three distinct processes and exchange messages only through s7085_inbox, s7085_tasks, s7085_drafts, and s7085_final. Preserve correlation_id and produce final JSON with status and answer.",
            body,
        ),
        Paragraph("Implementation", h2),
        Paragraph(
            "planner.py, writer.py, and reviewer.py are separate process entry points. Their __main__ paths invoke kafka_runtime.run_stage. Each stage uses its own input/output topic, a consumer group, manual commits after successful publication, and stage-specific message construction.",
            body,
        ),
        Paragraph("Actual code snippet: kafka_runtime.py / run_stage", h2),
        Preformatted(source("kafka_runtime.py", 65, 95), code),
        Paragraph("Code explanation", h2),
        Paragraph(
            "The planner creates a plan, the writer creates a draft, and the reviewer creates status=approved plus answer. KAFKA_GROUP_ID can be overridden so two Writer instances share a group during the ordering experiment. Correlation IDs are copied unchanged.",
            body,
        ),
        Paragraph("Runtime evidence", h2),
        Paragraph(
            "[LIVE SCREENSHOT MISSING] The source is wired for live Kafka, but Docker/Kafka was unavailable in this environment. The deterministic pipeline test is labeled [UNIT/OFFLINE] and does not prove consumer-group delivery.",
            caption,
        ),
        PageBreak(),
    ]

    story += [
        Paragraph("4. Part 3 - Duplicate delivery and idempotency", h1),
        Paragraph("Objective and rubric requirement", h2),
        Paragraph(
            "Replay the same correlation ID and demonstrate no additional side effect after the idempotency fix.", body
        ),
        Paragraph("Implementation and code", h2),
        Preformatted(source("kafka_protocol.py", 44, 68), code),
        Paragraph(
            "The processed map returns the original response when a correlation ID is replayed. The test asserts equality of both responses and side_effects == 1. This is [UNIT/OFFLINE] evidence, not a real Kafka replay capture.",
            body,
        ),
        Paragraph("Raw evidence", h2),
        Paragraph(
            "reports/hw08/raw/part3_failure_ordering.json records before=2, after=1, and idempotent=true. It is a deterministic artifact produced by failure_ordering.py; it does not claim a broker replay occurred.",
            body,
        ),
        Paragraph(
            "[LIVE SCREENSHOT MISSING] A real duplicate-delivery screenshot requires a running broker and a replay command.",
            caption,
        ),
        PageBreak(),
    ]

    story += [
        Paragraph("5. Part 3 - Consumer death and offsets", h1),
        Paragraph("Objective and rubric requirement", h2),
        Paragraph(
            "Terminate Writer during processing, restart it, show redelivery or completion, and demonstrate that offsets commit only after successful publication.",
            body,
        ),
        Paragraph("Implementation", h2),
        Paragraph(
            "kafka_runtime.run_stage constructs the consumer with enable_auto_commit=False, publishes the next-stage message, and calls consumer.commit() only afterward. This ordering is visible in the source and is covered by the deterministic failure artifact.",
            body,
        ),
        Preformatted(source("kafka_runtime.py", 58, 82), code),
        Paragraph("Evidence status", h2),
        Paragraph(
            "[UNIT/OFFLINE] The raw artifact records redelivery-after-restart and commit-after-success semantics. [LIVE UNVERIFIED] No Writer process was killed and restarted because the Kafka stack could not start. No screenshot is claimed.",
            body,
        ),
        PageBreak(),
    ]

    story += [
        Paragraph("6. Part 3 - Poison messages and dead letter", h1),
        Paragraph("Objective and rubric requirement", h2),
        Paragraph(
            "Retry a poison message within a bound, publish it to s7085_dead_letter, and continue processing a later valid message.",
            body,
        ),
        Paragraph("Implementation and artifact", h2),
        Paragraph(
            "DEAD_LETTER is a fixed PREFIX-prefixed topic in hw8_config.py. The deterministic artifact records retries=3, the dead-letter topic, and valid_following_message_processed=true. The current runtime still needs a live retry/dead-letter consumer implementation and broker run to satisfy this item fully.",
            body,
        ),
        Preformatted(source("hw8_config.py", 1, 18), code),
        Paragraph("Status", h2),
        Paragraph(
            "[PARTIAL] Topic configuration and offline evidence exist. Actual bounded retry and dead-letter publication are not directly verified live; the report does not claim otherwise.",
            body,
        ),
        PageBreak(),
    ]

    story += [
        Paragraph("7. Part 3 - Two-partition ordering", h1),
        Paragraph("Objective and rubric requirement", h2),
        Paragraph(
            "Generate exactly 20 related messages with VERIFY_SEED=267085, run two Writer instances in one group with two task partitions, compare no-key and related-entity-key runs, and save actual inputs, partitions, and outputs.",
            body,
        ),
        Paragraph("Implementation", h2),
        Paragraph(
            "docker-compose.hw8.yml creates s7085_tasks with two partitions. failure_ordering.py deterministically generates 20 IDs and compares shuffled no-key order with keyed order. KAFKA_GROUP_ID supports the shared consumer group. The deterministic result is useful for test repeatability but is not evidence of Kafka partition assignment.",
            body,
        ),
        Preformatted(source("failure_ordering.py", 1, 30), code),
        Paragraph("Status", h2),
        Paragraph(
            "[UNIT/OFFLINE] 20-message artifact exists. [LIVE UNVERIFIED] Actual partition numbers, two Writer processes, and broker processing order require Docker/Kafka and are missing.",
            body,
        ),
        PageBreak(),
    ]

    comparison = [
        ["Dimension", "HW2 in-process graph", "HW8 Kafka design"],
        ["Benefits", "Direct calls are simple", "Decoupling and independent process scaling"],
        ["Benefits", "Failure is local to call stack", "Messages can be redelivered after a consumer restart"],
        ["Responsibilities", "No broker offsets", "Manual offset commit after successful publication"],
        [
            "Responsibilities",
            "No duplicate delivery",
            "Idempotency, retries, dead-letter handling, and partition-key ordering",
        ],
    ]
    table = Table(comparison, colWidths=[1.0 * inch, 2.4 * inch, 2.9 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9eaf7")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story += [
        Paragraph("8. Kafka versus HW2", h1),
        Paragraph(
            "Kafka provides independent scaling and decoupled failure boundaries. It introduces responsibilities that HW2 function calls did not: idempotency for duplicate delivery, offset timing, bounded retries/dead-letter handling, and explicit partition-key ordering. The failure table below summarizes implemented control intent and evidence level.",
            body,
        ),
        table,
        PageBreak(),
    ]

    story += [
        Paragraph("9. Verification, artifacts, and limitations", h1),
        Paragraph("Commands actually run", h2),
        Preformatted(
            "pytest -q --cache-clear tests/test_hw8.py    -> 5 passed\npython verify_hw8.py                         -> exit 0\npython failure_ordering.py                    -> exit 0\npython -m compileall ...                     -> exit 0\nruff check <HW8 files>                        -> all checks passed\npython build_hw8_report.py                   -> exit 0",
            code,
        ),
        Paragraph("Tagged artifacts", h2),
        Paragraph(
            "reports/hw08/ contains Parab_HW8.pdf, RUN_LOG.txt, METRICS.md, AI_USE.md, REQUIREMENTS_CHECKLIST.md, EVIDENCE_MANIFEST.md, verification.json, and raw/part3_failure_ordering.json. verification.json records validation commit 6ad25857a674a2e38d8565d02a7dc9f7d0f13ea2 and four passing offline smoke checks.",
            body,
        ),
        Paragraph("Unverified requirements", h2),
        Paragraph(
            "Docker/Kafka live execution, real broker redelivery/offset behavior, live dead-letter publication, two-consumer partition evidence, required terminal screenshots, hardware specification, and collaborator access remain unverified. JMeter is supplementary demo material and was not run. The published hw8 tag remains unchanged while this completion branch is reviewed.",
            body,
        ),
        PageBreak(),
    ]

    story += [
        Paragraph("10. AI_USE disclosure", h1),
        Paragraph((REPORT_DIR / "AI_USE.md").read_text(encoding="utf-8"), body),
        Paragraph("11. Evidence index", h1),
        Paragraph(
            "No screenshot is represented as live when the runtime was unavailable. The missing-evidence statements above are intentional and correspond to the Docker and hardware checks recorded during this audit.",
            body,
        ),
    ]
    doc.build(story)


if __name__ == "__main__":
    build()
