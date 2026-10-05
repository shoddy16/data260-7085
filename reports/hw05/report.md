# Bhushan Waingankar - DATA 260 Homework 5

**Status: draft for evidence completion.** `Waingankar_HW5.pdf` is a formatted report based on the actual repository, raw result receipts, and the saved verification record. Yellow panels identify the exact GUI screenshots still needed; they are placeholders, not evidence. Add screenshots with the listed filenames under `reports/hw05/screenshots/` and rerun `build_report.py` to insert them.

## Project and environment

- Repository: https://github.com/shoddy16/data260-7085
- Branch: `hw5`
- Configuration: SID4 7085; PORT_BASE 8785; PREFIX s7085; SEED 7085; VERIFY_SEED 267085; DOMAIN_ID 5
- Hardware: Windows 10; Intel Core i5-6200U at 2.30 GHz; 4 logical CPUs; approximately 7.8 GB RAM
- Model: Ollama `llama3.2:3b` at `http://localhost:11434`
- Base HEAD at verification: `fb6884388a43142bf983566125e4fc0070ddf557`; it is not the final submission commit. The `hw5` tag is still pending.

## Part 1 - Database, API, and Redux

The existing FastAPI/MySQL service now models a one-to-many Restaurant-to-Inspection relationship. The additive migration preserved the existing data, added five inspection fields (`restaurant_id`, `inspection_code`, `score`, `created_at`, `updated_at`), backfilled restaurant references, and added a restrictive FK, unique inspection code, and indexes. Post-migration read-only checks found 5,000 inspections linked to 5,001 restaurants, including the pre-existing Harbor Cafe; there were no incomplete inspection links or duplicate inspection codes. Paginated API GET requests for both resources returned HTTP 200. The Python suite exercised creation, updates, deletion, conflict, not-found, and validation status paths. The Redux Toolkit frontend production build passed with 96 modules transformed.

## Part 2 - MCP servers

Actual MCP stdio discovery found four MealDB tools and exactly three domain tools (`search`, `detail_lookup`, `aggregate`). Live TheMealDB calls returned Spicy Arrabiata Penne (52771), Brown Stew Chicken (52940) and Chicken & chorizo rice pot (53161), Fish fofos (53043), and Teriyaki Chicken Casserole (52772). The domain server returned the common `{ok, data, error}` envelope for valid and invalid inputs. Receipts are retained in `raw/mealdb_live_results.json`, `raw/mcp_stdio_results.json`, and `raw/domain_tool_contract_cases.json`. Inspector screenshots are still required.

## Part 3 - Reliability

The actual seeded experiment ran 50 calls per failure rate (150 total), with three attempts, 50 ms base backoff, 200 ms cap, and 1 ms simulated operation work. Results: 0% injected failures - 100% success, 1.6720 ms mean, 4.1288 ms p99; 20% - 100%, 6.0630 ms, 37.4028 ms; 50% - 90%, 13.6744 ms, 37.1493 ms. Raw CSV/JSONL records and retry examples are retained in `raw/`. These are measurements of the local simulated workload, not a production service.

## Part 4 - Safe dispatcher and offline tests

`execute_tool()` is the single safe entry point and returns the shared envelope. The offline assertion runner passed 9/9 without Internet or a live model. The full Python unittest suite passed 24 tests. Fixture records demonstrate an allowed search and a safety-blocked request to evade or falsify an inspection. A MockModel run stopped after two steps at `max_steps`. Actual fixture outputs are saved in `raw/safety_examples.json` and `raw/max_steps_example.json`.

## Part 5 - Agent and reflection

Four focused real Ollama scenarios completed with `normal_completion`, two steps, and one tool call each: Restaurant 1/location search, inspection 4 detail lookup, category aggregate, and Sanitation-category query. Summaries and detailed events are in `raw/agent_scenario_summary.json` and `raw/agent_runs.jsonl`. An additional aggregate request timed out after producing a large result; the trace remains in the log and is not counted as a successful scenario. The 200-300 word reflection and AI-use answers appear in the PDF and the corresponding Markdown files.

## Verification and remaining work

The saved `verification.json` records 11 checks passing, including the 24 Python tests, 9 offline assertions, Vite build, actual migrated MySQL schema/data, paginated APIs, saved live MCP/MealDB receipts, four selected Ollama runs, and 150 experiment records. It correctly leaves `final_verification` and `submission_ready` false because no GUI screenshots have been saved and the final PDF, Git review, commit, and tag are pending. Collaborator access was not confirmed. See `EVIDENCE_CHECKLIST.md` for the exact manual capture checklist. Do not stage the pre-existing HW3 changes or unrelated user files during final Git review.
