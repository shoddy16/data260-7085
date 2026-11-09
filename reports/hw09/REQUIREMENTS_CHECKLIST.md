# HW9 requirements checklist

| Requirement | Implementation/evidence | Status |
|---|---|---|
| Part 1 Redis `INCR`, prefixed keys, tenth-write DB sync | `hw9_cache.py`, `routers/hw9.py`, `tests/test_hw9.py`, `raw/live_view_counter_mysql_redis.json` | live Redis/MySQL verified; concurrency verified |
| Part 2 ingress semantic cache and instrumentation | `hw9_cache.py`, `routers/hw9.py`, `tests/test_hw9.py`, `raw/live_semantic_cases.json`, `raw/embedding_probe_nomic.json`, `raw/live_knn_validation.json` | live Redis HNSW KNN verified with 768-dimensional vectors; exact/paraphrase hits, logical-difference/unrelated misses, stale guard, empty index, and concurrent lookups recorded |
| Part 3 frozen 40-case dataset and threshold sweep | `cache_cases.yaml`, commit `a7533e7d5eb1df286b77450ce7999d0ad6a5a12d`, `run_hw9_qualifying_sweep.py`, `raw/threshold_sweep_qualifying_knn.json` | qualifying post-commit live Ollama/Redis-KNN sweep passed at all five thresholds; final report update remains |
| Part 3 version-aware invalidation | `SemanticCache.invalidate_restaurant`, `raw/live_invalidation_mysql_redis.json` | live MySQL/Redis verified |
| Part 4 evaluator, bounded repair, lessons, four variants | `hw9_agents.py`, `run_hw9_agent_validation.py`, `raw/agent_validation.json` | verified with deterministic held-out inputs |
| Required runtime evidence | `reports/hw09/evidence/`, `reports/hw09/raw/` | live Swagger/health screenshots and raw service evidence present |
| Final PDF | `reports/hw09/Parab_HW9.pdf` | generated, rendered, and checked against the qualifying post-commit sweep |
