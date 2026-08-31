# DATA 260 HW1 Metrics- Shoury Parab

## Non-Determinism Experiment

Fixed input:
reports/hw01/cases/nondeterminism_input.json

Total runs:
40

| Metric | Temperature 0.7 | Temperature 0.0 |
|---|---:|---:|
| Runs | 20 | 20 |
| Distinct tag sets | 18 | 1 |
| Tags appearing in all 20 runs | None | restaurant inspections; local government; food safety |
| Tags appearing exactly once | 9 unique tags | None |
| Mean latency (ms) | 52313.27 | 43349.38 |
| p50 latency (ms) | 50517.81 | 43025.84 |
| p95 latency (ms) | 55879.40 | 43942.77 |
| p99 latency (ms) | 81676.63 | 47393.76 |

### Temperature of 0.7

Distinct tag sets: 18

Tags appearing exactly once:

- local business
- restaurant review
- web applications
- inspection report
- inspections
- reviews
- inspections and reviews
- restaurant inspection data
- local restaurants

### Temperature 0.0

Distinct tag sets: 1

Tags appearing in all 20 runs:

- restaurant inspections
- local government
- food safety

Tags appearing exactly once:

- None

### Latency Comparison

Mean latency at temperature 0.7: 52313.27 ms

Mean latency at temperature 0.0: 43349.38 ms

Temperature 0.7 was 20.68% slower than temperature 0.0.

### Interpretation
The experiment showed substantially greater variatio at temperature 0.7. The same input produced 18 distinct tag sets across 20 runs while temperature  of 0.0 produced exactly one tag set across all 20 runs.

Therefore two users submitting identical input could receive different tags and summaries when using a higher temperature. At temperature 0.0 the observed output was stable across all runs.

Run-to-run variation can be acceptable for exploratory tasks such as generating alternative descriptions or brainstorming topical labels. It would be less acceptable for a task such as producing a consistent compliance classification or safety-related decision where identical input should produce a predictable result.

The higher-temperature configuration was also way slower in this experiment with a mean latency increase of 20.68%.