# HW6 Rubric Audit

Audited against the official eight-page `DATA260_HW6.pdf` on 2026-10-09.

| Requirement | Evidence/status |
|---|---|
| Section 0 configuration, hardware, model, tagged hash | Configuration/model verified; hardware and tag added to the regenerated report. |
| Required `reports/hw06` files | Present: RUN_LOG.txt, raw/, METRICS.md, AI_USE.md, verification.json, and final PDF. |
| Part 1 MongoDB document schema and CRUD | Implemented in `hw6_mongo.py` and `routers/hw6.py`; FastAPI validation smoke checks pass. Live MongoDB collection/schema evidence is blocked because Docker Desktop/MongoDB is unavailable. |
| Part 1 invalid-data examples and collection screenshots | API 422 cases verified with TestClient; genuine MongoDB screenshots are still missing. |
| Part 2 ten-message real session | Offline ten-turn design exists; a real Ollama run was attempted but exceeded the execution timeout. MongoDB-backed messages/summaries/episodes are not verified. |
| Part 2 memory and aggregate JSON | Endpoints are implemented; live JSON responses require MongoDB. |
| Part 3 token/latency records | Raw 30-turn records and cost comparison are present. Latency is deterministic test-run latency, not a completed Ollama/MongoDB production measurement. |
| Part 3 probes and policy comparison | `memory_probes.yaml`, scoring summaries, compression comparison, and 10,000-conversation cost estimates are present. |
| Part 4 file memory and commands | `/memory`, `/compact`, `/dream`, `/help`, AGENT.md, and consolidation tests pass. |
| Part 4 55-line fixture and consolidation | Original fixture is exactly 55 lines; consolidated MEMORY.md has 32 nonblank/noncomment lines. Original and consolidated versions are committed. |
| Part 4 MongoDB-versus-file comparison | Comparison added to the final report. MongoDB persistence claims remain unverified. |
| AI_USE four questions | AI_USE.md contains all four numbered answers. |
| Tagged smoke verification | `verify_hw6.py` now requires HEAD to match the peeled `hw6` tag and runs objective API/validation checks without changing application code. |
| Collaborator access | Not verifiable from this environment; GitHub repository access settings require owner/account confirmation. |
| Final screenshots and submission readiness | Not complete: no genuine MongoDB/Compass or live memory screenshots were captured. |
