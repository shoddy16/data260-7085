# HW5 Metrics

## Part 3 — Fault Injection

Run started (UTC): 2026-10-05T09:00:59.207862+00:00
Seed: `267085`. Calls: 50 per configured transient-failure probability (150 total).
Retry policy: 3 attempts, 0.050s base delay, 0.200s delay cap.
Each attempt draws a seeded random value; a draw below the configured rate injects one transient failure.
Latency is measured from the actual local experiment call and includes attempt work and backoff sleep.

| Injected transient-failure probability | Calls | Success rate | Mean latency (ms) | p99 latency (ms) | Injected failures |
|---:|---:|---:|---:|---:|---:|
| 0% | 50 | 100.00% | 3.3442 | 15.9864 | 0 |
| 20% | 50 | 100.00% | 10.9706 | 116.0853 | 16 |
| 50% | 50 | 90.00% | 29.1529 | 180.6751 | 44 |

Retry behavior demonstrations are recorded in `fault_injection_summary.json`; all per-call attempts and measured latencies are in `raw/fault_injection_records.csv` and `.jsonl`.

### Suitability
The measured policy succeeded on all calls at 0% and 20% injected failure, while five of fifty calls still failed at 50%. The observed means were 3.3 ms, 11.0 ms, and 29.2 ms, respectively. This is a reasonable interactive policy when transient errors are uncommon, but the long-tail waits at 50% make it unsuitable to hide sustained service trouble. For batch work, I would consider a larger retry budget and longer capped backoff, while recording a per-item failure and continuing the batch; those values should be tuned with a separate measured run.
