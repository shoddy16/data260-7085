# HW7 Requirements Checklist

Source: `DATA260_HW7_final.docx`, seven pages, inspected before implementation.

## Submission and configuration

- [x] Record SID4-derived configuration values, hardware/model metadata, and current working-tree status.
- [x] Use the existing repository and root-level application folders.
- [x] Create `reports/hw07/` with `RUN_LOG.txt`, `raw/`, `METRICS.md`, `AI_USE.md`, `Parab_HW7.pdf`, and `verification.json`.
- [x] Include the repository link in the report; collaborator access remains unverified.
- [ ] Tag the submitted state `hw7` (deferred until final review/approval).

## Part 1

- [x] JWT login and `/auth/me`.
- [x] MySQL `users` table migration with username, hashed password, and reader/writer/moderator role.
- [x] Existing domain routes protected by role authorization.
- [x] 200/201, 401, and 403 behaviors demonstrated by tests.
- [x] Ruff and pre-commit configured; targeted HW7 checks pass.
- [x] Browser evidence for login, token failures, role-denied create/delete, successful create/delete, and authenticated list.
- [ ] Terminal screenshot showing lint failure, fixes, pre-commit during commit, and successful commit (commit intentionally not created in this phase).

## Part 2

- [x] Use HW1 model adapter and HW5 `search`, `detail_lookup`, and `aggregate` tool names/contracts.
- [x] Implement bounded `run_agent(user_input)` with tool-role results and total call logging.
- [x] Repair malformed arguments, unknown tools, and schema failures once with a bounded stop.
- [x] Run fixed multi-step cases A, B, and C plus recovery in deterministic evidence and capture the output.
- [x] Run 20 attempts and classify reliability failures.

## Part 3

- [x] Add bounded Reflexion with deterministic verifier.
- [x] Enforce maximum two retries, tool/token budgets, and stop reasons.
- [x] Store concise evidence-backed reflections without hidden chain-of-thought.
- [x] Compare original versus Reflexion outputs in raw/original_vs_reflexion.json.

## Part 4

- [x] Choose Citi Bike NYC as the supported city.
- [x] Implement read-only `csv_sql`, `policy_retriever`, and safe `calculator` tools.
- [x] Provide upload field, pricing URL field, Run button, timeline, result panel, citations, metrics, and stop reason.
- [x] Capture both completed UI scenarios.
- [x] Run two scenarios with at least 500 rows each: membership wins and pay-per-use wins.
- [x] Save pricing snapshot, URL, access timestamp, and SHA-256 hash.

## Part 5

- [x] Write a threat model with three attacker goals and enabling conditions.
- [x] Save a hostile local pricing-page fixture.
- [x] Test recommendation override, non-read-only SQL misuse, and CSV-content leakage.
- [x] Label retrieved text as untrusted data.
- [x] Enforce read-only `SELECT` at the tool boundary.
- [x] Report before/after results and explain tool-boundary versus prompt-only defense.

## Part 6

- [x] Implement `read_file`, `write_file`, `edit_file`, `glob_files`, `search_in_files`, and `bash` in a temporary sandbox.
- [x] Support `max_lines`, short edit diffs, and `file_pattern`.
- [x] Add `SAFE_PREFIXES`, `confirm_bash`, and independent `is_destructive` checks.
- [x] Run and capture glob → search → read integration test.
- [x] Run and capture five allowed and five blocked safety-gate commands.
- [x] No false allows remain in the deterministic command set.
