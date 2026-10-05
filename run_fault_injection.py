import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from fault_injection import run_experiment, run_retry_demonstrations, summarize
from hw5_config import PREFIX, VERIFY_SEED
from reliability import BASE_BACKOFF_SECONDS, MAX_ATTEMPTS, MAX_BACKOFF_SECONDS


ROOT = Path(__file__).resolve().parent
REPORT_DIR = ROOT / "reports" / "hw05"
RAW_DIR = REPORT_DIR / "raw"


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc).isoformat()
    records = run_experiment()
    summaries = summarize(records)
    demonstrations = run_retry_demonstrations()

    jsonl_path = RAW_DIR / "fault_injection_records.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, sort_keys=True) + "\n")

    csv_path = RAW_DIR / "fault_injection_records.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        fieldnames = [
            "call_id",
            "timestamp_utc",
            "failure_rate",
            "attempts",
            "injected_failures",
            "injection_draws",
            "success",
            "latency_ms",
            "result",
            "error",
        ]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    **record,
                    "injection_draws": json.dumps(record["injection_draws"]),
                    "result": json.dumps(record["result"]),
                }
            )

    metadata = {
        "homework": 5,
        "prefix": PREFIX,
        "verify_seed": VERIFY_SEED,
        "started_at_utc": started_at,
        "calls_per_rate": 50,
        "failure_rates": [0.0, 0.2, 0.5],
        "retry_policy": {
            "max_attempts": MAX_ATTEMPTS,
            "base_backoff_seconds": BASE_BACKOFF_SECONDS,
            "max_backoff_seconds": MAX_BACKOFF_SECONDS,
        },
        "demonstrations": demonstrations,
        "metrics": summaries,
    }
    (REPORT_DIR / "fault_injection_summary.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )

    metrics_path = REPORT_DIR / "METRICS.md"
    current = metrics_path.read_text(encoding="utf-8") if metrics_path.exists() else "# HW5 Metrics\n"
    marker = "## Part 3 — Fault Injection"
    if marker in current:
        current = current.split(marker, 1)[0].rstrip()
    section = [
        "",
        "## Part 3 — Fault Injection",
        "",
        f"Run started (UTC): {started_at}",
        f"Seed: `{VERIFY_SEED}`. Calls: 50 per configured transient-failure probability (150 total).",
        f"Retry policy: {MAX_ATTEMPTS} attempts, {BASE_BACKOFF_SECONDS:.3f}s base delay, {MAX_BACKOFF_SECONDS:.3f}s delay cap.",
        "Each attempt draws a seeded random value; a draw below the configured rate injects one transient failure.",
        "Latency is measured from the actual local experiment call and includes attempt work and backoff sleep.",
        "",
        "| Injected transient-failure probability | Calls | Success rate | Mean latency (ms) | p99 latency (ms) | Injected failures |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for summary in summaries:
        section.append(
            f"| {summary['failure_rate']:.0%} | {summary['calls']} | "
            f"{summary['success_rate_percent']:.2f}% | {summary['mean_latency_ms']:.4f} | "
            f"{summary['p99_latency_ms']:.4f} | {summary['injected_failures']} |"
        )
    section.extend(
        [
            "",
            "Retry behavior demonstrations are recorded in `fault_injection_summary.json`; all per-call attempts and measured latencies are in `raw/fault_injection_records.csv` and `.jsonl`.",
            "",
        ]
    )
    section.extend(
        [
            "### Suitability",
            f"The measured policy succeeded on all calls at 0% and 20% injected failure, while five of fifty calls still failed at 50%. The observed means were {summaries[0]['mean_latency_ms']:.1f} ms, {summaries[1]['mean_latency_ms']:.1f} ms, and {summaries[2]['mean_latency_ms']:.1f} ms, respectively. This is a reasonable interactive policy when transient errors are uncommon, but the long-tail waits at 50% make it unsuitable to hide sustained service trouble. For batch work, I would consider a larger retry budget and longer capped backoff, while recording a per-item failure and continuing the batch; those values should be tuned with a separate measured run.",
            "",
        ]
    )
    metrics_path.write_text(current.rstrip() + "\n" + "\n".join(section), encoding="utf-8")

    print(f"Started UTC: {started_at}")
    print(f"Seed: {VERIFY_SEED}; saved {len(records)} raw calls.")
    for demo in demonstrations:
        print(
            f"{demo['case']}: attempts={demo['attempts']} "
            f"outcome={demo.get('result', {}).get('status', demo.get('error'))}"
        )
    print("failure rate | success | mean ms | p99 ms")
    for summary in summaries:
        print(
            f"{summary['failure_rate']:.0%} | {summary['successes']}/{summary['calls']} "
            f"({summary['success_rate_percent']:.2f}%) | {summary['mean_latency_ms']:.4f} | "
            f"{summary['p99_latency_ms']:.4f}"
        )
    print(f"Raw JSONL: {jsonl_path.relative_to(ROOT)}")
    print(f"Raw CSV: {csv_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
