# HW8 Requirement-by-Requirement Audit

| Requirement | Implementation | Evidence | Status / next verification |
|---|---|---|---|
| Fixed personal configuration and restaurant domain | `hw8_config.py`, existing HW7 models | Unit imports and report metadata | Implemented; hardware query blocked |
| Exactly two RPC topics | `ENTITY_REQUESTS`, `ENTITY_RESPONSES` | `tests/test_hw8.py` | Implemented offline; verify with `kafka-topics` live |
| Request envelope and correlation preservation | `kafka_protocol.py`, `kafka_rpc.py` | Round-trip/error tests | Implemented offline; live flow unverified |
| CREATE_ENTITY UUID and dictionary storage | `EntityWorker.process` | `test_round_trip_and_correlation` | Implemented and directly unit-tested |
| GET_ENTITY and clean missing-ID error | `EntityWorker.process` | Round-trip/error tests | Implemented and directly unit-tested |
| Worker reply to `reply_to` | `kafka_runtime.run_entity_worker` | Source inspection | Implemented; live publish unverified |
| Full homework demo | `homework_demo.py` | Offline logs | Offline only; live sequence unverified |
| Kafka, worker, API running together | `docker-compose.hw8.yml`, `Dockerfile.hw8` | Docker command failed: engine unavailable | Blocked by environment |
| Three separate agent processes | `planner.py`, `writer.py`, `reviewer.py` | Entry-point/source inspection | Implemented; live Kafka journey unverified |
| Required four topics and two task partitions | compose topic initializer | Config/source inspection | Implemented; broker topic check unverified |
| Final status/answer JSON | `transform()` reviewer branch | Pipeline unit test | Offline verified |
| Duplicate idempotency | `EntityWorker.process.processed` | Raw artifact and unit test | Offline verified; broker replay unverified |
| Consumer death/redelivery/offset timing | manual commit after publish | Source only | Live behavior unverified |
| Poison retries/dead letter | `MAX_RETRIES`, `DEAD_LETTER` path | Topic/config artifact | Code added; live retry path unverified |
| Twenty-message ordering experiment | `failure_ordering.py` | JSON artifact with seed and partitions | Deterministic only; Kafka assignment unverified |
| HW2 comparison and failure table | report builder and METRICS | PDF/report text | Included; live rows incomplete |
| JMeter | supplementary instructions use port 8000 direct endpoint | JMeter PDF inspection | Not required by HW8 rubric; not run |
| Verification JSON | `verify_hw8.py` | `verification.json` | Offline smoke checks passed |
| Detailed report and screenshots | `build_hw8_report.py` | PDF | Report expanded; live screenshots missing |
| Hardware and collaborator access | environment/GitHub account | Access denied / gh unavailable | Unverified |
| Final `hw8` tag | published tag at `1b843e7...` | `git ls-remote` | Existing tag must not move without approval |
