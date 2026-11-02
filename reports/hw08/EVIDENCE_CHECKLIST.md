# HW8 Evidence Checklist

| Rubric evidence | Artifact | Status |
|---|---|---|
| Seven live Compose services | `evidence/docker_ps.txt` | Verified live |
| Kafka topic names | `evidence/topics.txt` | Verified live |
| `s7085_tasks` has two partitions | `evidence/tasks_description.txt` | Verified live |
| Worker/API startup | `evidence/service_logs.txt` | Verified live |
| CREATE/GET correlation and UUID | `evidence/live_entity.json` | Verified live |
| Planner → Writer → Reviewer correlation and final JSON | `evidence/live_pipeline.json` | Verified live |
| Poison retries, dead-letter, later valid message | `evidence/live_poison.json` | Verified live |
| Duplicate delivery in broker | none | Not verified live; offline unit only |
| Writer death/restart and offset redelivery | `evidence/consumer_death_crash_death-20261031-0056.log`, `evidence/consumer_death_recovery_death-20261031-0056.log`, `evidence/consumer_death_offsets_after_recovery_death-20261031-0056.txt`, `raw/live_consumer_death_hw8-death-death-20261031-0056.json` | Verified live; crash occurred before processing and same-group restart redelivered |
| 20-message unkeyed ordering experiment | `raw/live_ordering_order-20261031-0048_unkeyed.json`, `evidence/ordering_order-20261031-0048_writer_a.log`, `_writer_b.log`, group offsets | Verified live; both partitions used, no global-order claim |
| 20-message keyed ordering experiment | `raw/live_ordering_order-20261031-0052_keyed.json`, `evidence/ordering_order-20261031-0052_writer_a.log`, `_writer_b.log`, group offsets | Verified live; one key stayed on partition 1 and output sequence matched input |
| Required screenshots | none | Not captured; do not substitute logs |
| Scoped pytest suite | `RUN_LOG.txt` | 5 passed in rebuilt validation container |
| Scoped Ruff | `RUN_LOG.txt` | Passed in rebuilt validation container |
| JMeter supplementary demo | none | Not run |
| Hardware specification | none | Blocked by Windows access denied |
