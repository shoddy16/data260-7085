# HW7 Evidence Manifest

The UI screenshots were captured by Playwright Chromium against the running local Uvicorn application at `http://127.0.0.1:8785/hw7`. The API, agent, and file-tool captures show genuine outputs from the live API or deterministic project functions.

- `hw7_ui_initial.png`: initial upload form, pricing URL field, timeline panel, and empty result panel.
- `hw7_ui_pay_per_use_result.png`: uploaded `raw/pay_per_use_wins.csv`, four-step tool timeline, pay-per-use decision, costs, ride count, success stop reason, and citation link.
- `hw7_ui_membership_result.png`: uploaded `raw/membership_wins.csv`, four-step tool timeline, membership decision, costs, ride count, success stop reason, and citation link.
- `hw7_api_auth_roles_live.png`: live FastAPI successful/failed login, missing/invalid `/auth/me`, reader/writer/moderator create/delete, and authenticated list responses.
- `hw7_part2_tasks_and_recovery.png`: deterministic `run_agent` results for tasks A, B, C, and nonexistent-ID recovery.
- `hw7_part6_filetools_safety.png`: deterministic glob-search-read integration and five-allowed/five-blocked safety-gate outputs.

The screenshots are genuine captures. They were not generated or edited as illustrations. The professor-required terminal screenshot showing the lint failure/fix and successful commit remains unavailable because no commit was authorized in this phase and native terminal screenshot capture is unavailable.
