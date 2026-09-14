# HW2 Part 4 Metrics

## 30-run schema validation

| Outcome | Count | Mean latency (ms) |
|---|---:|---:|
| Valid first attempt | 30 | 18421.87 |
| Valid after 1 retry | 0 | 0.00 |
| Valid after 2+ retries | 0 | 0.00 |
| Hit turn ceiling | 0 | 0.00 |

## Turn ceiling comparison

| Ceiling | Runs | Completion rate | Mean latency (ms) |
|---:|---:|---:|---:|
| 2 | 20 | 100.0% | 17390.70 |
| 10 | 20 | 100.0% | 17413.83 |

## Adversarial test

- Runs: 5
- Completion rate: 100.0%
- Mean latency: 56118.27 ms

The adversarial input was used to test whether the validation and retry loop could recover from problematic Planner instructions.
