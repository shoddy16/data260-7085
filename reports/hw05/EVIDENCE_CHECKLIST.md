# HW5 Evidence Checklist

Save actual screen captures in `reports/hw05/screenshots/`. The directory currently contains **0** HW5 screenshots. Do not create substitute or mock images. For terminal captures, first run `Write-Host 'Bhushan Waingankar'` in the same terminal so the name is visible. Keep credentials and `.env` contents out of every frame.

## Part 1 — Database, API, and Redux

### MySQL database

- [ ] `P1-01-database-schema-and-rows.png` — Open the configured schema in MySQL Workbench (or the database GUI used for class). Show both `restaurants` and `inspections`, the relationship/FK definition, and linked rows. A read-only query pane may show:
  `SELECT COUNT(*) AS restaurant_count FROM restaurants;`
  `SELECT COUNT(*) AS inspection_count FROM inspections;`
  `SELECT i.id,i.inspection_code,i.restaurant_id,r.name,r.location,i.score FROM inspections i JOIN restaurants r ON r.id=i.restaurant_id ORDER BY i.id LIMIT 5;`
  Keep the connection/password panel hidden.

### Postman

Base URL: `http://localhost:8785`. Open the existing FastAPI project and use `http://localhost:8785/docs` to confirm the route list if needed. Create a temporary restaurant named `HW5 Evidence Cafe` in a test location and use only that newly created row for the remaining create/update/delete screenshots. Create one inspection linked to it. Delete only those temporary evidence records; first show the restrictive-delete response, then delete the child, then the parent.

Restaurant actions:

- [ ] `P1-02-restaurant-create.png` — `POST /restaurants/`, JSON `{"name":"HW5 Evidence Cafe","location":"San Jose"}`; show 201 and returned id/code.
- [ ] `P1-03-restaurant-list-pagination.png` — `GET /restaurants/?skip=0&limit=5`; show the page and query parameters.
- [ ] `P1-04-restaurant-detail.png` — `GET /restaurants/{new_id}`; show the returned record.
- [ ] `P1-05-restaurant-update.png` — `PUT /restaurants/{new_id}`, JSON `{"name":"HW5 Evidence Cafe Updated"}`; show 200 and updated record.
- [ ] `P1-06-restaurant-delete.png` — after the linked inspection is removed, `DELETE /restaurants/{new_id}`; show 204.

Inspection actions:

- [ ] `P1-07-inspection-create.png` — `POST /inspections/`, JSON with the new `restaurant_id`, `restaurantName`, `location`, `email`, `description`, `category`, and `score` (the Python API test provides a valid example); show 201 and nested restaurant.
- [ ] `P1-08-inspection-list-pagination.png` — `GET /inspections/?skip=0&limit=5`; show query parameters and records.
- [ ] `P1-09-inspection-detail.png` — `GET /inspections/{new_id}`; show the linked restaurant.
- [ ] `P1-10-inspection-update.png` — `PUT /inspections/{new_id}`, JSON `{"score":90}`; show 200 and updated score.
- [ ] `P1-11-inspection-delete.png` — `DELETE /inspections/{new_id}`; show 204.

Relationship and errors:

- [ ] `P1-12-relationship.png` — `GET /restaurants/{new_id}/inspections` before deleting the inspection; show the linked record.
- [ ] `P1-13-404.png` — `GET /restaurants/99999`; show 404.
- [ ] `P1-14-409.png` — while the temporary child exists, `DELETE /restaurants/{new_id}`; show restrictive-delete 409.
- [ ] `P1-15-validation.png` — `POST /restaurants/` with `{"name":"Bad Code","location":"San Jose","code":"wrong-format"}`; show 422.

### Redux UI

Run the frontend and backend locally. For each capture, arrange the relevant Redux thunk/slice code and browser UI response in the same frame.

- [ ] `P1-16-redux-home.png` — browser Home/list view plus list thunk/slice code.
- [ ] `P1-17-redux-create.png` — create flow and created record plus create thunk/slice code.
- [ ] `P1-18-redux-update.png` — update flow and changed record plus update thunk/slice code.
- [ ] `P1-19-redux-delete.png` — delete flow and resulting list plus delete thunk/slice code.

Migration/schema checks and read-only paginated GET endpoints already passed. API CRUD/status behavior passed automated tests. The Postman requests and visual UI screenshots still need manual capture.

## Part 2 — MCP Inspector

Open the actual MCP Inspector browser tab and connect it to the Meals server, then the restaurant domain server. Each capture must show Inspector, selected tool, exact input, and its actual returned output. Use the previously verified calls below or fresh calls to the same live tools.

- [ ] `P2-01-meal-search.png` — `search_meals_by_name`, query `Arrabiata`, limit 2.
- [ ] `P2-02-meal-ingredient.png` — `meals_by_ingredient`, ingredient `chicken`, limit 2.
- [ ] `P2-03-meal-random.png` — `random_meal`, no arguments.
- [ ] `P2-04-meal-details.png` — `meal_details`, id `52772`.
- [ ] `P2-05-domain-search-ok.png` — valid `search`, query `Restaurant 1`, limit 2.
- [ ] `P2-06-domain-search-invalid.png` — invalid `search`, blank query.
- [ ] `P2-07-domain-detail-ok.png` — valid `detail_lookup`, inspection_id `4`.
- [ ] `P2-08-domain-detail-invalid.png` — invalid `detail_lookup`, inspection_id `0`.
- [ ] `P2-09-domain-aggregate-ok.png` — valid `aggregate`, group_by `category`.
- [ ] `P2-10-domain-aggregate-invalid.png` — invalid `aggregate`, group_by `email`.

Inspector discovery and real calls were performed. Captured JSON receipts are in `raw/mcp_stdio_results.json` and `raw/mealdb_live_results.json`. The Inspector GUI screenshots still need saving.

## Part 3 — Reliability

In the repository terminal, show “Bhushan Waingankar,” run `python run_fault_injection.py`, and capture the experiment output and metrics.

- [ ] `P3-01-fault-injection-run.png` — show all 150 calls and each rate (0%, 20%, 50%; 50 calls each).
- [ ] `P3-02-retry-examples.png` — open/show the actual success, retry-success, and exhausted-retry entries from `reports/hw05/fault_injection_summary.json`.
- [ ] `P3-03-metrics.png` — show success rate, mean latency, and p99 from `reports/hw05/METRICS.md`.

Raw records already exist in `raw/fault_injection_records.csv` and `.jsonl`.

## Part 4 — Safe Entry Point and Offline Tests

- [ ] `P4-01-offline-tests.png` — at repository root run `Write-Host 'Bhushan Waingankar'; .\.venv\Scripts\python.exe run_offline_tests.py`; capture every PASS line and final `9/9`.
- [ ] `P4-02-safety-allowed.png` — show the actual allowed test result/envelope from the offline runner.
- [ ] `P4-03-safety-blocked.png` — show the actual blocked safety result/envelope from the offline runner.
- [ ] `P4-04-max-steps.png` — show the MockModel runaway test and `max_steps` stop from the offline runner.

The latest Python suite passed 24/24, and the offline runner passed 9/9.

## Part 5 — Agent and final report

- [ ] `P5-01-agent-scenarios.png` — at repository root run `Write-Host 'Bhushan Waingankar'; Get-Content reports\hw05\raw\agent_scenario_summary.json`; show all four prompts, step counts, stop reasons, and tool-call counts. The saved runs are real Ollama runs.
- [ ] `P5-02-agent-log.png` — show the corresponding actual run entries in `reports\hw05\raw\agent_runs.jsonl`.
- [ ] Save `reports/hw05/Waingankar_HW5.pdf` after all screenshot images are inserted. The PDF needs 14 pt bold main headings, 12 pt bold subheadings, and 11 pt body text; include `AI_USE.md` content and all required sections/evidence.

## Capture status

No HW5 screenshots have been saved yet. The database GUI, Postman, Redux browser/code, MCP Inspector, and terminal captures require user-visible desktop interaction. Save each image with the listed filename under `reports/hw05/screenshots/`. After capture, rerun the verification script and only then prepare the final PDF and Git commit/tag.
