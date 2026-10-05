"""Reproducible transient-failure experiment for the HW5 retry policy."""

import random
import time
from datetime import datetime, timezone
from typing import Any

from hw5_config import VERIFY_SEED
from reliability import retry_sync


class InjectedTransientFailure(RuntimeError):
    pass


def simulate_one_call(
    *,
    rng: random.Random,
    failure_rate: float,
    call_id: str,
    max_attempts: int = 3,
    base_backoff_seconds: float = 0.01,
    max_backoff_seconds: float = 0.04,
    sleep=time.sleep,
    attempt_work_seconds: float = 0.001,
) -> dict[str, Any]:
    draws = []
    start = time.perf_counter()
    timestamp_utc = datetime.now(timezone.utc).isoformat()

    def operation():
        draw = rng.random()
        draws.append(draw)
        if attempt_work_seconds:
            time.sleep(attempt_work_seconds)
        if draw < failure_rate:
            raise InjectedTransientFailure("transient fault injected")
        return {"status": "ok"}

    error = None
    result = None
    try:
        result = retry_sync(
            operation,
            max_attempts=max_attempts,
            base_backoff_seconds=base_backoff_seconds,
            max_backoff_seconds=max_backoff_seconds,
            should_retry=lambda exc: isinstance(exc, InjectedTransientFailure),
            sleep=sleep,
        )
        succeeded = True
    except InjectedTransientFailure as exc:
        succeeded = False
        error = str(exc)

    latency_ms = (time.perf_counter() - start) * 1000
    return {
        "call_id": call_id,
        "timestamp_utc": timestamp_utc,
        "failure_rate": failure_rate,
        "attempts": len(draws),
        "injected_failures": sum(draw < failure_rate for draw in draws),
        "injection_draws": [round(draw, 8) for draw in draws],
        "success": succeeded,
        "latency_ms": round(latency_ms, 4),
        "result": result,
        "error": error,
    }


def run_experiment(
    *,
    seed: int = VERIFY_SEED,
    calls_per_rate: int = 50,
    failure_rates: tuple[float, ...] = (0.0, 0.2, 0.5),
    sleep=time.sleep,
    attempt_work_seconds: float = 0.001,
) -> list[dict[str, Any]]:
    records = []
    for rate in failure_rates:
        rng = random.Random(seed)
        rate_label = int(rate * 100)
        for index in range(1, calls_per_rate + 1):
            records.append(
                simulate_one_call(
                    rng=rng,
                    failure_rate=rate,
                    call_id=f"{rate_label:02d}-{index:03d}",
                    sleep=sleep,
                    attempt_work_seconds=attempt_work_seconds,
                )
            )
    return records


def summarize(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for rate in sorted({record["failure_rate"] for record in records}):
        selected = [record for record in records if record["failure_rate"] == rate]
        latencies = sorted(record["latency_ms"] for record in selected)
        p99_index = max(0, min(len(latencies) - 1, int((0.99 * len(latencies) + 0.999999)) - 1))
        successes = sum(record["success"] for record in selected)
        summaries.append(
            {
                "failure_rate": rate,
                "calls": len(selected),
                "successes": successes,
                "success_rate_percent": round(100 * successes / len(selected), 2),
                "mean_latency_ms": round(sum(latencies) / len(latencies), 4),
                "p99_latency_ms": latencies[p99_index],
                "injected_failures": sum(record["injected_failures"] for record in selected),
            }
        )
    return summaries


def run_retry_demonstrations() -> list[dict[str, Any]]:
    outcomes = []

    attempts = {"count": 0}

    def succeeds_first_try():
        attempts["count"] += 1
        return {"status": "ok"}

    result = retry_sync(succeeds_first_try)
    outcomes.append({"case": "first_attempt_success", "attempts": attempts["count"], "result": result})

    attempts["count"] = 0

    def succeeds_after_retry():
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise InjectedTransientFailure("one transient failure")
        return {"status": "ok"}

    result = retry_sync(succeeds_after_retry)
    outcomes.append({"case": "retry_then_success", "attempts": attempts["count"], "result": result})

    attempts["count"] = 0

    def always_fails():
        attempts["count"] += 1
        raise InjectedTransientFailure("all attempts failed")

    try:
        retry_sync(always_fails)
    except InjectedTransientFailure as exc:
        outcomes.append(
            {
                "case": "failure_after_retries",
                "attempts": attempts["count"],
                "error": str(exc),
            }
        )
    return outcomes
