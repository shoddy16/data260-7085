"""Build the detailed HW9 PDF and editable DOCX from verified artifacts."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepInFrame,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "reports" / "hw09"
RAW = REPORT_DIR / "raw"
EVIDENCE = REPORT_DIR / "evidence"
PDF_OUT = REPORT_DIR / "Parab_HW9.pdf"
DOCX_OUT = REPORT_DIR / "Parab_HW9.docx"


def load_json(name: str):
    return json.loads((RAW / name).read_text(encoding="utf-8"))


def source_snippet(relative: str, start: int, end: int) -> str:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    result = []
    for number, line in enumerate(lines[start - 1 : end], start):
        wrapped = textwrap.wrap(line, width=96, subsequent_indent="       ") or [""]
        result.append(f"{number:03}: {wrapped[0]}")
        result.extend(wrapped[1:])
    return "\n".join(result)


def para(text: str, style):
    return Paragraph(text.replace("&", "&amp;"), style)


def report_styles():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle", parent=styles["Title"], fontSize=20, leading=25, alignment=TA_CENTER, spaceAfter=14
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle", parent=styles["Normal"], fontSize=13, leading=16, alignment=TA_CENTER, spaceAfter=12
        ),
        "h1": ParagraphStyle(
            "ReportH1",
            parent=styles["Heading1"],
            fontSize=14,
            leading=18,
            spaceBefore=8,
            spaceAfter=8,
            textColor=colors.HexColor("#234f7d"),
        ),
        "h2": ParagraphStyle(
            "ReportH2",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            spaceBefore=6,
            spaceAfter=6,
            textColor=colors.HexColor("#326b9e"),
        ),
        "body": ParagraphStyle("ReportBody", parent=styles["BodyText"], fontSize=11, leading=14, spaceAfter=7),
        "small": ParagraphStyle("ReportSmall", parent=styles["BodyText"], fontSize=9, leading=11, spaceAfter=5),
        "caption": ParagraphStyle(
            "ReportCaption",
            parent=styles["BodyText"],
            fontSize=9.5,
            leading=12,
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "code": ParagraphStyle(
            "ReportCode",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=6.7,
            leading=7.8,
            textColor=colors.whitesmoke,
        ),
        "output": ParagraphStyle(
            "ReportOutput",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor("#202020"),
        ),
    }


def dark_panel(text: str, style) -> Table:
    content = KeepInFrame(7.0 * inch, 650, [Preformatted(text, style)], mode="shrink")
    return Table(
        [[content]],
        colWidths=[7.05 * inch],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#17191c")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#56616d")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        ),
    )


def light_panel(text: str, style) -> Table:
    content = KeepInFrame(7.0 * inch, 650, [Preformatted(text, style)], mode="shrink")
    return Table(
        [[content]],
        colWidths=[7.05 * inch],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f1f1")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#b7b7b7")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        ),
    )


def data_table(rows, widths=None) -> Table:
    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#234f7d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#c8c8c8")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f6f9")]),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def figure(name: str, caption: str, width=6.9 * inch, height=None):
    path = EVIDENCE / name
    if not path.exists():
        return [para(f"Figure unavailable: {name}", STYLES["small"])]
    if height is None:
        from PIL import Image as PILImage

        with PILImage.open(path) as image:
            ratio = image.height / image.width
        height = width * ratio
    return [Image(str(path), width=width, height=height), para(caption, STYLES["caption"])]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(0.65 * inch, 0.38 * inch, "DATA 260 - Homework 9 - Shoury Ambarish Parab")
    canvas.drawRightString(7.85 * inch, 0.38 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf() -> None:
    global STYLES
    STYLES = report_styles()
    counter = load_json("live_view_counter_mysql_redis.json")
    live_cases = load_json("live_semantic_cases.json")
    knn = load_json("live_knn_validation.json")
    qualifying = load_json("threshold_sweep_qualifying_knn.json")
    variants = load_json("self_improvement_variants.json")
    agent = load_json("agent_validation.json")
    invalidation = load_json("live_invalidation_mysql_redis.json")

    story = []
    h1, h2, body = STYLES["h1"], STYLES["h2"], STYLES["body"]
    code, output = STYLES["code"], STYLES["output"]

    # Cover and contents
    story += [
        Spacer(1, 0.35 * inch),
        para("DATA 260", STYLES["title"]),
        para("HOMEWORK 9", STYLES["title"]),
        para("Redis Semantic Caching and Self-Improving Multi-Agent System", STYLES["subtitle"]),
        Spacer(1, 0.15 * inch),
        para("Shoury Ambarish Parab", STYLES["subtitle"]),
        para("SID4: 7085", STYLES["subtitle"]),
        para("Repository: https://github.com/shoddy16/data260-7085", STYLES["subtitle"]),
        Spacer(1, 0.2 * inch),
    ]
    config = [
        ["Setting", "Verified value"],
        ["PREFIX", "s7085"],
        ["SEED", "7085"],
        ["VERIFY_SEED", "267085"],
        ["DOMAIN_ID", "5"],
        ["PORT_BASE / HW9_PORT", "8085 / 8086"],
        ["Chat / embedding", "llama3.2:3b / nomic-embed-text"],
        ["Embedding dimension", "768"],
        ["Backend", "FastAPI, SQLAlchemy, Redis Stack, Ollama"],
    ]
    story += [
        data_table(config, [2.15 * inch, 4.9 * inch]),
        Spacer(1, 0.2 * inch),
        para(
            "This report presents my completed HW9 implementation and the evidence collected for each part. It distinguishes live Redis/Ollama/MySQL results, deterministic local experiments, unit tests, and reproducibility artifacts.",
            body,
        ),
        PageBreak(),
    ]
    story += [para("Contents", h1)]
    contents = [
        "1. Project context and architecture",
        "2. Part 1 - Redis restaurant view counter",
        "3. Part 2 - Redis semantic response cache",
        "4. Part 3 - Frozen dataset and threshold economics",
        "5. Stale-answer invalidation",
        "6. Part 4 - Self-improving agents",
        "7. Testing and regression audit",
        "8. Required artifacts and reproducibility",
        "9. AI use and verification",
        "10. Final checklist and conclusion",
    ]
    story += [para("<br/>".join(contents), body), PageBreak()]

    # 1
    story += [
        para("1. Project context and architecture", h1),
        para(
            "I extended the existing restaurant-inspection application rather than creating a separate project. HW9 adds a Redis view counter, a semantic response cache in front of the existing Q&A path, a frozen threshold experiment, and a reference-backed evaluator loop. The previous HW2 report used PORT_BASE=8785. The current HW9 configuration is verified in hw9_config.py and Compose: PORT_BASE=8085 and HW9_PORT=8086, with Redis exposed on host port 6380.",
            body,
        ),
        para(
            "The request flow is: restaurant access -> Redis INCR -> periodic database synchronization. A question -> Ollama embedding -> Redis HNSW KNN -> similarity and safeguards -> cached answer or existing answer path. The self-improvement experiment is separate from live model latency and uses reference data to make its outcomes repeatable.",
            body,
        ),
        dark_panel(source_snippet("hw9_config.py", 1, 20), code),
        para("Figure 1. Configuration excerpt from hw9_config.py.", STYLES["caption"]),
        para(
            "The hardware query was restricted in this environment, so I do not report an unverified CPU or memory specification. Python 3.10.2 was observed during the earlier live validation. Docker Engine 29.9.2 and the local Ollama runtime were available for the live Redis and embedding checks.",
            body,
        ),
        PageBreak(),
    ]

    # Part 1 subsections
    story += [
        para("2. Part 1 - Redis-backed restaurant view counter", h1),
        para(
            "Requirement. Every restaurant access must increment Redis with INCR, use the s7085 prefix, synchronize the relational row every tenth view, return the current count, and handle missing records, Redis failures, rollback, and concurrency.",
            body,
        ),
        para(
            "Implementation. ViewCounter.increment_restaurant_views builds s7085:views:restaurant:{id}. Redis INCR is atomic for one key, so concurrent requests receive distinct counts. The database is touched only when count % 10 == 0. This reduces database write pressure while keeping the twentieth view persisted.",
            h2,
        ),
        dark_panel(source_snippet("hw9_cache.py", 42, 61), code),
        para(
            "The code catches Redis errors and raises a runtime error for the route to translate into HTTP 503. A missing Restaurant row raises ValueError. A failed commit rolls back the session before re-raising.",
            body,
        ),
        light_panel(json.dumps(counter, indent=2), output),
        para("Figure 2. Live Redis/MySQL view-counter output.", STYLES["caption"]),
        para(
            "The recorded counts were 1, 2, 10, 20, and 21. The database remained at 20 after the twenty-first access, which is the expected every-tenth-write behavior. The concurrent run produced 20 unique Redis counts and database_views=20.",
            body,
        ),
        PageBreak(),
    ]
    story += [
        para("2.1 API route, errors, and concurrency", h2),
        dark_panel(source_snippet("routers/hw9.py", 114, 128), code),
        para(
            "The route injects a database session and the current user, then maps ValueError to 404 and Redis/runtime failures to 503. The response returns restaurant_id and views. The focused tests also exercise independent IDs and a broken Redis client. The live evidence and the in-memory concurrency test support the atomic-increment claim; they do not claim that the database is synchronized on every request.",
            body,
        ),
        data_table(
            [
                ["Check", "Observed result"],
                ["Redis key", counter["redis_key"]],
                ["Counts", str(counter["counts_1_2_10_20_21"])],
                ["Database after 21", str(counter["database_views_after_21"])],
                ["Tenth sync", str(counter["tenth_sync"])],
                ["Concurrent unique counts", str(counter["concurrent_unique_counts"])],
                ["Concurrent database views", str(counter["concurrent_database_views"])],
            ],
            [2.6 * inch, 4.45 * inch],
        ),
        para("Figure 3. Part 1 verification table.", STYLES["caption"]),
        PageBreak(),
    ]

    # Part 2
    story += [
        para("3. Part 2 - Redis semantic response cache", h1),
        para(
            "The cache sits at the ingress of /hw9/ask. It embeds the incoming question with nomic-embed-text, searches the Redis HNSW index, converts Redis cosine distance to similarity, checks the threshold, and then applies query-signature, restaurant-scope, and data-version safeguards. A hit returns the stored answer without calling the answerer. A miss invokes the existing agent path and stores the answer and metadata.",
            body,
        ),
        para(
            "The field alias embedding_vector is important. The previous index used the JSON path as its identifier and returned no usable KNN matches. I migrated the index without deleting JSON records and recreated it with an explicit alias and DIM=768.",
            h2,
        ),
        dark_panel(source_snippet("hw9_cache.py", 141, 178), code),
        PageBreak(),
    ]
    story += [
        para("3.1 KNN lookup and similarity conversion", h2),
        dark_panel(source_snippet("hw9_cache.py", 238, 274), code),
        para(
            "Redis Search returns vector_distance for a COSINE index. The implementation computes 1 - distance, clamps the value to the valid similarity range, and rejects malformed distances. It then loads the document by Redis ID and checks data_version, signature, and restaurant_id before accepting the result. A live Redis client never silently falls back to a Python scan. The only explicit scan fallback is the MemoryRedis unit-test backend, which is labeled offline_test_backend.",
            body,
        ),
        light_panel(json.dumps(knn, indent=2), output),
        para(
            "Figure 4. Live Redis KNN validation output, including index metadata and backend confirmation.",
            STYLES["caption"],
        ),
        PageBreak(),
    ]
    story += [
        para("3.2 Cache integration and safeguards", h2),
        dark_panel(source_snippet("routers/hw9.py", 96, 111), code),
        para(
            "The route derives a coarse query signature for score predicates. This does not replace semantic similarity; it prevents an above query from reusing a below query answer. The restaurant_id check prevents cross-restaurant reuse. The data-version value is captured on write and compared during lookup. These guards are necessary because embeddings measure language similarity, not whether two questions have identical answer semantics.",
            body,
        ),
        data_table(
            [
                ["Live case", "Similarity", "Cached", "Agent executed"],
                *[
                    [
                        r["category"].replace("_", " "),
                        f"{r['body']['similarity']:.6f}",
                        str(r["body"]["is_cached"]),
                        str(r["body"]["agent_executed"]),
                    ]
                    for r in live_cases["cases"]
                ],
            ],
            [2.2 * inch, 1.3 * inch, 1.0 * inch, 1.55 * inch],
        ),
        para("Figure 5. Live semantic-cache cases.", STYLES["caption"]),
        PageBreak(),
    ]
    story += [
        para("3.3 Embedding, empty-index, and concurrent validation", h2),
        para(
            "The live KNN validation used the configured 768-dimensional embedding model. Exact and paraphrase queries matched the temporary restaurant-scoped record. Logical and unrelated queries were rejected by signature filtering. After incrementing the temporary restaurant version, the old record was rejected. An isolated empty index produced a miss, and eight concurrent queries all reported the Redis KNN backend.",
            body,
        ),
        data_table(
            [
                ["Case", "Result"],
                ["Exact", "hit, similarity 1.0"],
                ["Paraphrase", "hit, similarity 0.9385986"],
                ["Logical difference", "miss"],
                ["Unrelated", "miss"],
                ["Stale version", "rejected after version increment"],
                ["Empty index", "miss"],
                ["Concurrent", "8/8 KNN lookups"],
            ],
            [2.0 * inch, 5.05 * inch],
        ),
        para(
            "Redis errors are surfaced as RuntimeError rather than silently producing a scan result. Invalid embedding vectors are rejected before packing or ignored when Redis returns an invalid distance.",
            body,
        ),
        PageBreak(),
    ]

    # Part 3
    story += [
        para("4. Part 3 - Frozen dataset and threshold economics", h1),
        para(
            "The qualifying experiment used the committed cache_cases.yaml at commit a7533e7d5eb1df286b77450ce7999d0ad6a5a12d. The file contains 40 restaurant-inspection cases: ten exact duplicates, ten paraphrases, ten similar questions with different answers, and ten unrelated questions. The expected distribution is 20 hits and 20 misses. No labels were changed after the preliminary sweep.",
            body,
        ),
        data_table(
            [
                ["Category", "Count", "Expected"],
                ["Exact duplicate", "10", "hit"],
                ["Paraphrase", "10", "hit"],
                ["Similar, different answer", "10", "miss"],
                ["Unrelated", "10", "miss"],
                ["Total", "40", "20 hit / 20 miss"],
            ],
            [3.0 * inch, 1.1 * inch, 2.95 * inch],
        ),
        para("Figure 6. Frozen case distribution.", STYLES["caption"]),
        para(
            "The experiment stores one set of reference answers, runs the same 40 cases at each threshold, and uses the live Ollama provider and Redis KNN backend for every row. Hit rate is hits/40. False-hit rate is false hits/20 expected-miss cases. Cost is (40 - hits)*1 + false_hits*8.",
            body,
        ),
        PageBreak(),
    ]
    sweep_rows = [
        ["Threshold", "Hits", "Misses", "Correct", "False", "Missed hits", "Hit rate", "False/20", "Mean ms", "Cost"]
    ]
    for row in qualifying["thresholds"]:
        sweep_rows.append(
            [
                f"{row['threshold']:.2f}",
                str(row["cache_hits"]),
                str(row["cache_misses"]),
                str(row["correct_hits"]),
                str(row["false_hits"]),
                str(row["missed_expected_hits"]),
                f"{row['hit_rate']:.3f}",
                f"{row['false_hit_rate']:.3f}",
                f"{row['mean_latency_ms']:.2f}",
                f"{row['total_cost']:.0f}",
            ]
        )
    story += [
        para("4.1 Qualifying five-threshold sweep", h2),
        data_table(
            sweep_rows,
            [
                0.55 * inch,
                0.5 * inch,
                0.55 * inch,
                0.55 * inch,
                0.5 * inch,
                0.65 * inch,
                0.6 * inch,
                0.65 * inch,
                0.7 * inch,
                0.45 * inch,
            ],
        ),
        para("Figure 7. Final qualifying threshold results.", STYLES["caption"]),
        para(
            "The cost decreases from 83 to 51 as the threshold increases. The decrease is not free: 0.95 keeps only 13 hits and misses ten cases that were labeled expected hits. The lowest-cost threshold is therefore a measured choice under this cost model, not a universal correctness guarantee.",
            body,
        ),
        PageBreak(),
    ]
    story += [
        para("4.2 False-hit analysis and latency interpretation", h2),
        para(
            "The qualifying sweep recorded a real live false hit at every threshold. At 0.75, the cached question was 'Which restaurant scored above 90?' and the incoming question was 'Which restaurants scored above 70?'. The similarity was 0.869723975658, so the cached answer was returned even though the numeric predicate changed. The wording shares restaurant, score, and comparison language, which explains the high embedding similarity. Query signatures reduce this risk, but a richer structured predicate check would be safer.",
            body,
        ),
        light_panel(json.dumps(qualifying["thresholds"][0]["false_hit_examples"], indent=2), output),
        para("Figure 8. Recorded qualifying false-hit example.", STYLES["caption"]),
        para(
            "The 0.75 mean latency was 2537.92 ms, much higher than the other rows. The raw artifact does not include per-case timing samples or a separate cold-start marker, so the exact cause cannot be proven. The most plausible explanation is first-use Ollama embedding/model overhead, because the provider cache is cold at the beginning of the sweep. The reported value is end-to-end lookup time for each case, including embedding generation and Redis KNN, not pure Redis KNN latency.",
            body,
        ),
        PageBreak(),
    ]
    story += [
        para("4.3 Threshold recommendation", h2),
        para(
            "Under the required cost model, I would ship 0.95 as the measured lowest-cost threshold. I would keep the signature, restaurant-scope, and data-version checks enabled and would not interpret 0.95 as sufficient by itself: three false hits remain and ten expected hits are missed. A production policy could require a higher-confidence threshold plus structured predicate validation for score, date, and restaurant filters.",
            body,
        ),
        para(
            "The separate fallback false_hit_example.json is retained as historical diagnostic evidence only. It is not used as the qualifying live Ollama false-hit example. The qualifying result above is the primary evidence.",
            body,
        ),
        PageBreak(),
    ]

    # stale
    story += [
        para("5. Stale-answer experiment and version invalidation", h1),
        para(
            "The live MySQL/Redis sequence cached a restaurant answer, changed the real restaurant location, queried again without invalidation, and observed the old answer. The restaurant data version was then incremented. The next query missed the old cache entry and returned the updated location. The invalidation is scoped to one restaurant instead of deleting every cache record.",
            body,
        ),
        dark_panel(source_snippet("hw9_cache.py", 203, 235), code),
        light_panel(json.dumps(invalidation, indent=2), output),
        para("Figure 9. Live stale-answer and data-version evidence.", STYLES["caption"]),
        para(
            "Version markers are preferable to a global delete because unrelated restaurant answers can remain available. The trade-off is that writes must increment the correct version marker; a missed increment can leave stale data available.",
            body,
        ),
        PageBreak(),
    ]

    # Part 4
    story += [
        para("6. Part 4 - Self-improving multi-agent system", h1),
        para(
            "The Answering Agent reads the reference dataset and optional lessons. The Evaluator Agent compares an answer with the reference fact. A REVISE result allows exactly one revised answer and a second evaluation. A successful repair can create a lesson, but lesson validation must prevent a local improvement from damaging previously correct or unrelated questions.",
            body,
        ),
        dark_panel(source_snippet("hw9_agents.py", 69, 112), code),
        para("Figure 10. SelfImprovingSystem repair loop excerpt.", STYLES["caption"]),
        PageBreak(),
    ]
    story += [
        para("6.1 Dataset separation and bounded repair", h2),
        para(
            "training_data.json, validation_data.json, and test_data.json contain questions only. Expected facts are kept in reference_data.json. The held-out test questions are used for comparison, not for lesson creation or prompt tuning. The controlled repair used the question 'Which restaurants scored below 70?'. The first answer was intentionally incorrect, the evaluator returned REVISE with a verified fact, the revised answer passed, and the run used two attempts.",
            body,
        ),
        light_panel(json.dumps(agent["bounded_repair"], indent=2), output),
        para("Figure 11. Controlled repair result.", STYLES["caption"]),
        PageBreak(),
    ]
    story += [
        para("6.2 Lesson persistence, reuse, and validation", h2),
        para(
            "Lessons contain lesson_id, failure_pattern, correction, created_at, and use_count. The controlled run recorded one created lesson and use_count=1 after reuse. A deliberately rejected lesson was not retained. The current lessons.json may be reset by later experiments, so the raw agent_validation.json is the authoritative record for the reuse event.",
            body,
        ),
        light_panel(
            "lesson_count_after_repair: 1\nlesson_use_count_after_reuse: 1\nrejected_lesson_file_exists: false", output
        ),
        para("Figure 12. Lesson creation and rejection evidence.", STYLES["caption"]),
        PageBreak(),
    ]
    variant_rows = [["Variant", "Correct", "Incorrect", "Avg attempts", "Avg latency ms"]]
    for row in variants:
        variant_rows.append(
            [
                row["variant"].replace("_", " ").title(),
                str(row["correct_answers"]),
                str(row["incorrect_answers"]),
                f"{row['average_attempts']:.2f}",
                f"{row['average_latency_ms']:.4f}",
            ]
        )
    story += [
        para("6.3 Four-variant comparison", h2),
        data_table(variant_rows, [2.35 * inch, 0.8 * inch, 0.8 * inch, 1.2 * inch, 1.55 * inch]),
        para("Figure 13. Four variants evaluated on the same ten-question held-out set.", STYLES["caption"]),
        para(
            "Baseline produced 9/10 correct. Evaluator Repair, Lesson Memory, and Validated Improvement produced 10/10. The average attempts are calculated from individual runs. The timing boundary uses time.perf_counter around the local answer/evaluation path; it includes deterministic reference operations and lesson-file work where applicable, but not Ollama network latency. The values are therefore local execution timings, not LLM service benchmarks. Validated Improvement was strongest on accuracy, but the sample is small and does not establish generalization.",
            body,
        ),
        PageBreak(),
    ]

    # tests, evidence, reproducibility
    story += [
        para("7. Testing and regression audit", h1),
        data_table(
            [
                ["Command/check", "Result", "Status", "Notes"],
                [
                    "python -m pytest tests/test_hw9.py -q",
                    "4 passed",
                    "PASS",
                    "View counter, cache safeguards, bounded agents",
                ],
                ["ruff check scoped HW9 files", "All checks passed", "PASS", "Includes KNN and report builders"],
                ["python -m compileall ...", "Exit 0", "PASS", "Relevant source and scripts"],
                ["docker compose ... config --quiet", "Exit 0", "PASS", "Compose syntax"],
                ["live_knn_validation.py", "status PASS", "PASS", "Redis KNN, stale, empty, concurrent"],
                ["qualifying sweep", "five rows redis_knn=true", "PASS", "Live Ollama and Redis"],
                [
                    "SQLite regression suite",
                    "40 passed, 2 failures",
                    "PARTIAL",
                    "Earlier failures retained and disclosed",
                ],
                [
                    "Full default suite",
                    "collection blocked",
                    "RECORDED",
                    "Local MySQL authentication configuration",
                ],
            ],
            [2.7 * inch, 1.8 * inch, 0.8 * inch, 1.75 * inch],
        ),
        para("Figure 14. Test and verification matrix.", STYLES["caption"]),
        para(
            "The focused HW9 suite is green. The broader earlier-homework suite was not fully green: 40 tests passed and two failed, and the default suite could not complete collection under the local MySQL authentication configuration. I do not relabel those outcomes as a complete repository pass.",
            body,
        ),
        PageBreak(),
    ]
    story += [
        para("8. Runtime evidence and required artifacts", h1),
        para(
            "The runtime figures show the live Swagger surface and health response, while the source panels show relevant excerpts from the final HW9 files. The raw JSON files provide the detailed view-counter, semantic-cache, KNN, stale-invalidation, agent, threshold, Redis-index, and Docker results.",
            body,
        ),
        *figure("fig01_live_fastapi_docs.png", "Figure 15. Live FastAPI Swagger surface.", height=5.8 * inch),
        PageBreak(),
    ]
    story += [
        para("8.1 Reproducibility", h2),
        dark_panel(
            "docker compose -f docker-compose.hw9.yml up -d --build\npython -m pytest tests/test_hw9.py -q\nruff check hw9_cache.py hw9_agents.py routers/hw9.py tests/test_hw9.py\npython -m compileall -q hw9_cache.py hw9_agents.py routers/hw9.py\npython run_hw9_live_knn_validation.py\npython run_hw9_qualifying_sweep.py\ndocker compose -f docker-compose.hw9.yml config --quiet",
            code,
        ),
        para(
            "The qualifying sweep should not be rerun casually because live embedding calls are slow and the result is already preserved. The command is recorded for reproducibility, not as a request to change the committed dataset or labels.",
            body,
        ),
        *figure("fig02_hw9_endpoints_crop.png", "Figure 16. HW9 endpoint group in Swagger UI.", height=3.9 * inch),
        PageBreak(),
    ]
    story += [
        para("9. AI use disclosure and verification", h1),
        para((REPORT_DIR / "AI_USE.md").read_text(encoding="utf-8").replace("\n", "<br/>"), body),
        para(
            "Dataset-freeze verification: commit a7533e7d5eb1df286b77450ce7999d0ad6a5a12d contains only cache_cases.yaml. The final package includes the HW9 implementation, experiments, report, and supporting evidence on the dedicated hw9 branch. Protected tags remain hw6=0307ac55b1ec9d6e48561a43e5671e21c09fd708, hw7=b78001eaa5c0f071eaf1788702c019d67983860a, and hw8=1b843e76d268dd9076230411e098e96ed43b9a8f.",
            body,
        ),
        PageBreak(),
    ]

    # final checklist
    story += [
        para("10. Final rubric checklist and conclusion", h1),
        data_table(
            [
                ["Requirement", "Status", "Evidence"],
                ["Redis INCR, prefix, tenth-write sync", "PASS", "Live view JSON, source, focused tests"],
                ["Redis error and missing-restaurant handling", "PASS", "Source and unit tests"],
                ["Concurrent view increments", "PASS", "Live counter JSON"],
                ["Semantic cache at /hw9/ask", "PASS", "Live API JSON and route/source"],
                ["Actual Redis HNSW KNN", "PASS", "live_knn_validation.json; qualifying rows"],
                ["Signatures, scope, data versions", "PASS", "KNN source and stale evidence"],
                ["Frozen dataset committed before sweep", "PASS", "Commit a7533e7"],
                ["Five-threshold live sweep", "PASS", "threshold_sweep_qualifying_knn.json"],
                ["False-hit analysis", "PASS", "Qualifying false-hit records"],
                ["Stale-answer invalidation", "PASS", "live_invalidation_mysql_redis.json"],
                ["Bounded two-attempt repair", "PASS", "agent_validation.json and source"],
                ["Lesson reuse and validation", "PASS", "agent_validation.json"],
                ["Four independent variants", "PASS", "self_improvement_variants.json"],
                ["Source excerpts and runtime figures", "PASS", "Report panels and live evidence"],
                ["Regression results", "PASS", "Focused HW9 and recorded broader-suite results"],
            ],
            [3.0 * inch, 1.15 * inch, 3.0 * inch],
        ),
        para(
            "The HW9 implementation, qualifying live KNN sweep, and supporting experiments are included in this submission. The measured lowest-cost threshold is 0.95, with the accuracy trade-off shown in the results table. The four-variant timings measure deterministic local answer, evaluation, and lesson-file work, so they are reported as local execution measurements rather than model-service benchmarks.",
            body,
        ),
        para(
            "Artifact inventory: source files at the repository root; datasets under data/hw9; machine-readable evidence under reports/hw09/raw; runtime images under reports/hw09/evidence; RUN_LOG.txt, METRICS.md, AI_USE.md, EVIDENCE_MANIFEST.md, and REQUIREMENTS_CHECKLIST.md under reports/hw09.",
            body,
        ),
    ]
    doc = SimpleDocTemplate(
        str(PDF_OUT),
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.62 * inch,
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def build_docx() -> None:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Inches, Pt, RGBColor

    qualifying = load_json("threshold_sweep_qualifying_knn.json")
    variants = load_json("self_improvement_variants.json")

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)
    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(11)
    for style_name, size, color in [("Title", 20, None), ("Heading 1", 14, "234F7D"), ("Heading 2", 12, "326B9E")]:
        style = doc.styles[style_name]
        style.font.name = "Arial"
        style.font.size = Pt(size)
        style.font.bold = True
        if color:
            style.font.color.rgb = RGBColor.from_string(color)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("DATA 260 - Homework 9 - Shoury Ambarish Parab")
    doc.add_heading("DATA 260 Homework 9", 0)
    doc.add_paragraph("Redis Semantic Caching and Self-Improving Multi-Agent System", style="Subtitle")
    doc.add_paragraph("Shoury Ambarish Parab\nSID4: 7085\nhttps://github.com/shoddy16/data260-7085")
    doc.add_paragraph(
        "Configuration: PREFIX=s7085, SEED=7085, VERIFY_SEED=267085, DOMAIN_ID=5, PORT_BASE=8085, HW9_PORT=8086, chat=llama3.2:3b, embeddings=nomic-embed-text (768 dimensions)."
    )
    doc.add_page_break()
    sections = [
        (
            "1. Project context and architecture",
            "I extended the shared restaurant-inspection application. HW9 adds a Redis view counter, Redis HNSW KNN semantic caching, a frozen threshold experiment, and a reference-backed evaluator loop. The report separates live service results from deterministic local experiments.",
        ),
        (
            "2. Part 1 - Redis-backed restaurant view counter",
            "ViewCounter uses Redis INCR with s7085:views:restaurant:{id}. It writes the Restaurant row every tenth count and returns the current Redis count. Live results recorded counts 1, 2, 10, 20, and 21, with database_views=20 after the twenty-first request and 20 unique concurrent counts.",
        ),
        (
            "3. Part 2 - Redis semantic response cache",
            "The /hw9/ask route embeds the query, runs Redis HNSW KNN, converts cosine distance to similarity, and applies signature, restaurant-scope, and data-version guards. Live KNN evidence recorded exact and paraphrase hits, logical and unrelated misses, stale rejection, empty-index miss, and concurrent KNN use.",
        ),
        (
            "4. Part 3 - Frozen dataset and threshold economics",
            "The committed cache_cases.yaml contains 40 cases in the required 10/10/10/10 distribution. The qualifying live sweep used nomic-embed-text and Redis KNN at all five thresholds. The measured costs were 83, 76, 77, 66, and 51; 0.95 was lowest but sacrificed valid hits.",
        ),
        (
            "5. Stale-answer invalidation",
            "A live MySQL/Redis experiment observed an old answer before version invalidation and the updated answer after the restaurant data-version marker was incremented. The scope is per restaurant rather than a global cache delete.",
        ),
        (
            "6. Part 4 - Self-improving agents",
            "The evaluator uses separate reference facts, the repair loop is bounded to two attempts, lessons contain the required fields, and the four variants use the same ten-question held-out set. Evaluator Repair, Lesson Memory, and Validated Improvement reached 10/10 in the deterministic experiment.",
        ),
        (
            "7. Testing and regression audit",
            "Focused HW9 tests, scoped Ruff, compileall, Compose configuration, live KNN validation, and the qualifying sweep passed. The broader SQLite suite had 40 passes and two failures; the full default suite was blocked by local MySQL authentication configuration.",
        ),
        (
            "8. Required artifacts and reproducibility",
            "Raw JSON is under reports/hw09/raw, runtime screenshots are under reports/hw09/evidence, and the checklists, metrics, run log, and AI disclosure are under reports/hw09.",
        ),
        (
            "9. AI use and verification",
            "AI assistance supported repository inspection, implementation drafting, test writing, and report editing. I reviewed and ran the implementation and distinguish live evidence from offline deterministic evidence. Dataset commit a7533e7d5eb1df286b77450ce7999d0ad6a5a12d contains only cache_cases.yaml.",
        ),
        (
            "10. Final checklist and conclusion",
            "The core HW9 behavior is verified, the qualifying KNN sweep is complete, and threshold 0.95 is the lowest-cost measured choice under the required model. The report includes the implementation excerpts, live runtime evidence, raw experiment outputs, and the measured timing methodology.",
        ),
    ]
    for heading, text in sections:
        doc.add_heading(heading, 1)
        doc.add_paragraph(text)
        if heading.startswith("2. Part 1") and (EVIDENCE / "fig02_hw9_endpoints_crop.png").exists():
            doc.add_picture(str(EVIDENCE / "fig02_hw9_endpoints_crop.png"), width=Inches(6.4))
            doc.add_paragraph("Figure. HW9 endpoint surface used for the live route checks.", style="Caption")
        if heading.startswith("3. Part 2"):
            doc.add_paragraph(
                "KNN validation summary: backend=redis_knn; index=s7085:semantic_cache_idx_v768; dimension=768; exact similarity=1.000000; paraphrase similarity=0.938599; logical-difference and unrelated cases missed; stale entry rejected after a version increment."
            )
        if heading.startswith("4. Part 3"):
            table = doc.add_table(rows=1, cols=6)
            table.style = "Table Grid"
            for cell, value in zip(
                table.rows[0].cells, ["Threshold", "Hits", "Correct", "False hits", "Mean ms", "Cost"]
            ):
                cell.text = value
            for row in qualifying["thresholds"]:
                cells = table.add_row().cells
                vals = [
                    f"{row['threshold']:.2f}",
                    str(row["cache_hits"]),
                    str(row["correct_hits"]),
                    str(row["false_hits"]),
                    f"{row['mean_latency_ms']:.2f}",
                    str(row["total_cost"]),
                ]
                for cell, value in zip(cells, vals):
                    cell.text = value
        if heading.startswith("6. Part 4"):
            table = doc.add_table(rows=1, cols=5)
            table.style = "Table Grid"
            for cell, value in zip(table.rows[0].cells, ["Variant", "Correct", "Incorrect", "Attempts", "Latency ms"]):
                cell.text = value
            for row in variants:
                cells = table.add_row().cells
                vals = [
                    row["variant"],
                    str(row["correct_answers"]),
                    str(row["incorrect_answers"]),
                    f"{row['average_attempts']:.2f}",
                    f"{row['average_latency_ms']:.4f}",
                ]
                for cell, value in zip(cells, vals):
                    cell.text = value
        doc.add_paragraph(
            "Source excerpts and machine-readable evidence for this section are retained in the repository under the source paths and reports/hw09/raw. The PDF contains the detailed tables, excerpts, and runtime figures."
        )
        doc.add_page_break()
    doc.save(DOCX_OUT)


if __name__ == "__main__":
    build_pdf()
    build_docx()
    print(PDF_OUT)
    print(DOCX_OUT)
