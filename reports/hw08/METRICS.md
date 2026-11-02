# HW8 Metrics

| Measure | Result | Status |
|---|---:|---|
| RPC topics | 2 | Live broker list verified |
| Agent topics | 4 | Live broker list verified |
| Ordering messages | 20 | Deterministic VERIFY_SEED=267085 run |
| Duplicate side effects | 1 after replay | Offline unit verified |
| Poison retries | 3 | Live dead-letter capture verified |
| Live services | 7/7 | Compose ps captured; Kafka healthy |
| Task partitions | 2 | Live kafka-topics describe verified |
| Live pipeline records | 3 | task, draft, final share one correlation ID |
| Live entity IDs | UUID | Live CREATE/GET capture verified |
| Consumer death recovery | 1 message | Live same-group redelivery and recovery verified |
| Ordering unkeyed | 20 messages | Live two Writer members; both partitions used; no global-order claim |
| Ordering keyed | 20 messages | Live all records on one partition; output sequence preserved |
| JMeter metrics | unavailable | Not measured |

The live captures are under `evidence/` and `raw/`. The earlier deterministic artifact remains separate from these broker measurements. The live ordering result demonstrates per-partition/key ordering only; it does not claim total ordering across partitions.

Live run IDs: consumer death `death-20261031-0056`; unkeyed ordering `order-20261031-0048`; keyed ordering `order-20261031-0052`. All ordering runs used `VERIFY_SEED=267085` and exactly 20 messages.
