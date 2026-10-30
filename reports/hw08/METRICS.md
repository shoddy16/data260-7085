# HW8 Metrics

| Measure | Result | Status |
|---|---:|---|
| RPC topics | 2 | Implemented; live broker pending |
| Agent topics | 4 | Implemented; live broker pending |
| Ordering messages | 20 | Deterministic VERIFY_SEED=267085 run |
| Duplicate side effects | 1 after replay | Offline unit verified |
| Poison retries | 3 | Offline artifact recorded |
| JMeter metrics | unavailable | Not measured |

Live-service metrics are intentionally absent because the Docker Desktop engine was unavailable. The 20-message ordering artifact is deterministic and records inputs plus a stable keyed partition calculation; it is not a Kafka broker measurement.
