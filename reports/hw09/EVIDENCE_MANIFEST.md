# HW9 evidence manifest

Genuine screenshots are stored under `reports/hw09/evidence/`:

- `fig01_live_fastapi_docs.png`: live FastAPI Swagger UI and existing domain routes.
- `fig02_hw9_api_endpoints.png`: full live Swagger UI capture.
- `fig02_hw9_endpoints_crop.png`: focused crop showing the HW9 endpoint group.
- `fig03_hw9_health_response.png`: live `/hw9/health` JSON response showing Redis.

Genuine machine-readable/live outputs are stored under `reports/hw09/raw/`:

- `embedding_probe_nomic.json`: numeric 768-dimensional Ollama vector probe and direct paraphrase cosine.
- `live_semantic_cases.json`: live exact, duplicate, paraphrase, logical-difference, and unrelated API cases.
- `threshold_sweep.json`: live five-threshold sweep using `nomic-embed-text` and the frozen 40 cases.
- `threshold_sweep_qualifying_knn.json`: qualifying post-commit sweep using the committed dataset, live `nomic-embed-text`, and Redis KNN; includes all required counts, rates, costs, and false-hit examples.
- `live_knn_validation.json`: live Redis KNN exact, paraphrase, logical-difference, unrelated, stale-version, empty-index, and concurrent-query results.
- `redis_index_info_v768.txt` and `redis_keys_v768.txt`: migrated HNSW schema and prefixed-key evidence.
- Existing Docker, MySQL/Redis view, invalidation, agent, and API raw outputs.

The index migration removed the stale 64-dimensional index and recreated the
versioned 768-dimensional index in the isolated HW9 Redis instance. The current
index metadata reports DIM=768 and zero current indexing failures. No screenshot
file is represented as a substitute for these raw artifacts.

The report places the source excerpts beside the corresponding runtime and raw
evidence so that each implementation decision can be followed from code to
observed result.
