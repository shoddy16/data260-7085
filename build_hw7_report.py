"""Build the HW7 report from the current source and evidence artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).parent
REPORT = ROOT / "reports" / "hw07"
OUT = REPORT / "Parab_HW7.pdf"
RAW = REPORT / "raw"

styles = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=16, leading=19, alignment=TA_CENTER, spaceAfter=6),
    "main": ParagraphStyle("main", fontName="Helvetica-Bold", fontSize=14, leading=17, spaceBefore=10, spaceAfter=5),
    "sub": ParagraphStyle("sub", fontName="Helvetica-Bold", fontSize=12, leading=15, spaceBefore=7, spaceAfter=3),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=11, leading=14, spaceAfter=5),
    "caption": ParagraphStyle("caption", fontName="Helvetica-Oblique", fontSize=11, leading=14, spaceBefore=2, spaceAfter=7),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=8.5, leading=10.5, leftIndent=8, rightIndent=8, spaceAfter=5),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=9, leading=11),
}


def p(text, style="body"):
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), styles[style])


def rich(text, style="body"):
    return Paragraph(text, styles[style])


def code(text):
    return Preformatted(text, styles["code"])


def img(name, caption):
    path = REPORT / name
    width, height = ImageReader(str(path)).getSize()
    scale = min(6.55 * inch / width, 4.9 * inch / height, 1)
    return [Image(str(path), width=width * scale, height=height * scale), p(caption, "caption")]


def table(rows, widths):
    converted = [[rich(str(cell), "small") for cell in row] for row in rows]
    result = Table(converted, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#9aa8b5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef3f8")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return result


verification = json.loads((REPORT / "verification.json").read_text(encoding="utf-8"))
scenarios = json.loads((RAW / "bike_share_scenarios.json").read_text(encoding="utf-8"))

story = [
    p("DATA 260 - Homework 7", "title"),
    p("Bhushan Waingankar | SID4 7085", "sub"),
    p("Repository: https://github.com/shoddy16/data260-7085"),
    p("Configuration: SID4=7085; PORT_BASE=8785; PREFIX=s7085; SEED=7085; VERIFY_SEED=267085; DOMAIN_ID=5"),
    p("Hardware: Windows 10; Intel Core i5-6200U at 2.30 GHz; 4 logical CPUs; approximately 7.8 GB RAM (recorded in the existing HW5/HW6 report artifacts)."),
    p("Local model: Ollama llama3.2:3b. Validated implementation/evidence commit: 85d98f4. A separate packaging commit will carry this metadata before the hw7 tag is created. The existing hw6 tag remains unchanged."),
    p("Implementation, verification, evidence, and limitations", "sub"),
    p("This report separates deterministic offline evidence, live local FastAPI/browser evidence, and checks that were not possible because MySQL, MongoDB, Ollama, repository-wide lint, or final Git submission was unavailable."),
    p("1. Source materials and requirements", "main"),
    p("The official DATA260_HW7_final.docx was read completely: seven pages, all paragraphs and three tables. DATA236_DEMO7.zip was readable: 6,943 entries and 31,983,746 bytes. Inspected reference material included its README, Ruff/pre-commit configuration, FastAPI JWT/RBAC routes, fake database, tests, and CI workflow. The ZIP is a generic reference and does not contain the HW1/HW5 agent, Reflexion, bike-share, prompt-injection, or file-tool implementation."),
    p("2. Implementation and code snippets", "main"),
    p("Part 1 - JWT and role authorization", "sub"),
    code("# jwt_auth.py\npassword_hash = hash_password(password)\nuser = authenticate_user(db, username, password)\nreturn create_access_token(user.username, user.role)\n\n# route policy\nreader: list/read\nwriter or moderator: create/update\nmoderator: delete"),
    p("The existing domain routes use bearer authentication. Automated API tests cover successful and failed login, missing authentication, reader denial, writer creation, authenticated listing, writer delete denial, and moderator delete success. The migration source creates the MySQL users fields and stores hashed passwords, but a live MySQL migration was not run."),
    p("Part 2 - Handwritten agent loop", "sub"),
    code("result = run_agent(user_input, model=model, tool_executor=execute_tool)\n# each tool result is appended with role=tool\n# max_steps and max_repairs bound execution"),
    p("The loop validates search, detail_lookup, and aggregate actions, retries one malformed action, records tool calls, and returns a bounded stop reason. The captured deterministic evidence covers A, B, C, and nonexistent-ID recovery; no live Ollama call is claimed."),
    p("Part 3 - Bounded Reflexion", "sub"),
    code("passed, reason = verify_task(task, result)\nif not passed: store concise evidence-backed reflection and retry\nmax_retries = 2; stop_reason in {success, human_review, budget_exhausted}"),
    p("The verifier accepts the final A/B/C deterministic results. Unsupported-claim counts and token counts are unavailable because the scripted model exposes no token accounting and no claim extractor was implemented. False verifier rejections were 0/3 final results; the first intentionally incomplete attempts were rejected before successful retries."),
    p("Part 4 - Citi Bike MRKL tools", "sub"),
    code("csv_sql(sql) -> read-only SELECT over uploaded CSV\npolicy_retriever(url, query, k) -> short cited passages\ncalculator(expression) -> whitelisted arithmetic only\ncommon result shape: success, data, error, source, ts"),
    p("The UI accepts one CSV and pricing URL, shows the tool timeline, cost comparison, decision, citation, step count, and stop reason. The two deterministic cases use 600 and 500 rows and the official pricing snapshot hash."),
    p("Part 5 - Prompt injection", "sub"),
    code("retrieved pricing text is labeled untrusted data\ncsv_sql accepts one read-only SELECT statement regardless of model text\nraw CSV rows are not included in the final recommendation"),
    p("The local hostile pricing fixture exercises recommendation override, non-read-only SQL, and CSV-content inclusion. Full attack traces are in the raw JSON artifact."),
    p("Part 6 - File tools and safety gate", "sub"),
    code("read_file, write_file, edit_file, glob_files, search_in_files, bash\nSAFE_PREFIXES allow-list plus independent is_destructive deny-list\nconfirm_bash(command, auto_approve=False) -> allow/block and reason"),
    p("The integration test creates Python files, performs glob -> search -> read, and the safety test checks five allowed and five blocked commands. The final raw result contains no false allows in that deterministic set."),
    PageBreak(), p("3. Verification and metrics", "main"),
]

story.append(table([
    ["Check", "Actual result"],
    ["HW7/API/HW6 regression tests", "11 passed in the combined pytest run; later split runs recorded 5 and 5 due the repository test-run environment."],
    ["Targeted Ruff", "Passed on HW7/API files; exit 0."],
    ["Targeted pre-commit", "Passed Ruff check and Ruff format on HW7 files; exit 0."],
    ["Compileall", "Passed: python -m compileall -q ."],
    ["Deterministic evidence", "Six checks passed: two scenarios, differing decisions, 20 attempts, injection artifact, file integration, and 5/5 safety gate."],
    ["Live local app", "GET /hw7 and the 500-row API scenario returned HTTP 200."],
    ["Unavailable checks", "Live MySQL, MongoDB, Ollama, full-repository Ruff/pre-commit, and final Git submission were not completed."],
], [2.0 * inch, 4.55 * inch]))
story += [Spacer(1, 8), p("Bike-share metrics", "sub")]
story.append(table([
    ["Scenario", "Rows", "Decision", "Pay/use", "Membership + residual", "Steps/stop"],
    ["membership_wins", "600", scenarios["membership_wins"]["decision"], "$7,480", "$2,669", "4 / success"],
    ["pay_per_use_wins", "500", scenarios["pay_per_use_wins"]["decision"], "$100", "$239", "4 / success"],
], [1.25 * inch, .55 * inch, 1.55 * inch, .7 * inch, 1.15 * inch, 1.0 * inch]))
story += [p("Reliability: 20/20 deterministic calls were well formed before and after repair; classification counts were none=20 and all other failure classes=0. Token counts are unavailable, not zero. Unsupported-claim metrics are unavailable because no claim ledger exists. Pricing snapshot SHA-256: 8a1c1952ab94c6a3820c3d7ee2aac7c9b5d9fd6ebc52d69937e2996785b5a9de.")]

story += [PageBreak(), p("4. Required evidence screenshots", "main")]
for name, caption in [
    ("hw7_api_auth_roles_live.png", "Figure 1. Live browser evidence from the running FastAPI application: successful/failed login, missing and invalid token, role-denied create/delete, successful writer create, authenticated list, and moderator delete."),
    ("hw7_ui_membership_result.png", "Figure 2. Live Citi Bike UI membership-winning case: four-step timeline, decision, cost comparison, 600 rides, citation, and success stop reason."),
    ("hw7_ui_pay_per_use_result.png", "Figure 3. Live Citi Bike UI pay-per-use case: four-step timeline, decision, cost comparison, 500 rides, citation, and success stop reason."),
    ("hw7_part2_tasks_and_recovery.png", "Figure 4. Deterministic run_agent evidence for tasks A, B, C, and nonexistent-ID recovery."),
    ("hw7_part6_filetools_safety.png", "Figure 5. Deterministic file-tool integration and ten-command safety-gate output."),
]:
    if (REPORT / name).exists():
        story += img(name, caption)

story += [PageBreak(), p("5. Raw artifacts and command record", "main")]
story += [p("The following artifacts are included under reports/hw07/raw/: agent_reliability_20.csv, original_vs_reflexion.json, bike_share_scenarios.json, membership_wins.csv, pay_per_use_wins.csv, citi_bike_pricing_snapshot.txt, hostile_pricing_fixture.html, prompt_injection_before_after.json, and file_tools_and_safety.json.")]
story += [p("RUN_LOG.txt records deterministic evidence generation, targeted tests, lint/pre-commit checks, compileall, and live local browser capture. METRICS.md records measured values and explicitly labels unavailable token and unsupported-claim metrics. AI_USE.md answers the four required disclosure questions. verification.json contains SID4, seeds, model, checks, and the validated implementation commit 85d98f4.")]
story += [p("6. Limitations and submission sequencing", "main")]
story += [p("The report records the validated implementation/evidence commit 85d98f4. The final packaging commit contains only the verified commit metadata and regenerated report; the hw7 tag will point to that packaging commit. This two-commit sequence avoids claiming that a commit contains its own unknowable hash. Live MySQL, MongoDB, and Ollama/model verification remains unavailable. The professor-required lint-failure-before-commit terminal screenshot remains unavailable because native terminal screenshot capture is unavailable.")]
story += [p("After the packaging commit, Git verification must confirm that hw7 points to the packaging commit and that origin/hw6 still points to 0307ac55b1ec9d6e48561a43e5671e21c09fd708.")]
story += [p("Evidence manifest", "sub"), p("Screenshots and supporting files are enumerated in reports/hw07/EVIDENCE_MANIFEST.md. The report does not claim that unavailable live services or unperformed commit/tag actions succeeded.")]

OUT.parent.mkdir(parents=True, exist_ok=True)
SimpleDocTemplate(str(OUT), pagesize=letter, rightMargin=.55 * inch, leftMargin=.55 * inch, topMargin=.5 * inch, bottomMargin=.5 * inch).build(story)
print(OUT)
