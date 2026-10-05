import asyncio
import random
import unittest

from fault_injection import InjectedTransientFailure, run_experiment, simulate_one_call
from reliability import retry_async, retry_sync


class RetryPolicyTests(unittest.TestCase):
    def test_first_attempt_success_does_not_sleep(self):
        calls = {"count": 0}

        def operation():
            calls["count"] += 1
            return "ok"

        result = retry_sync(operation, sleep=lambda _delay: self.fail("unexpected retry"))
        self.assertEqual(result, "ok")
        self.assertEqual(calls["count"], 1)

    def test_transient_failure_retries_with_exponential_delays(self):
        calls = {"count": 0}
        delays = []

        def operation():
            calls["count"] += 1
            if calls["count"] == 1:
                raise InjectedTransientFailure("retry me")
            return "ok"

        result = retry_sync(
            operation,
            base_backoff_seconds=0.01,
            max_backoff_seconds=0.02,
            sleep=delays.append,
        )
        self.assertEqual(result, "ok")
        self.assertEqual(calls["count"], 2)
        self.assertEqual(delays, [0.01])

    def test_retry_limit_returns_final_failure(self):
        calls = {"count": 0}
        delays = []

        def operation():
            calls["count"] += 1
            raise InjectedTransientFailure("still failing")

        with self.assertRaisesRegex(InjectedTransientFailure, "still failing"):
            retry_sync(operation, sleep=delays.append)
        self.assertEqual(calls["count"], 3)
        self.assertEqual(delays, [0.05, 0.1])

    def test_failure_injection_sequence_repeats_for_fixed_seed(self):
        first = run_experiment(
            seed=267085,
            calls_per_rate=12,
            sleep=lambda _delay: None,
            attempt_work_seconds=0,
        )
        second = run_experiment(
            seed=267085,
            calls_per_rate=12,
            sleep=lambda _delay: None,
            attempt_work_seconds=0,
        )
        self.assertEqual(
            [(row["failure_rate"], row["injection_draws"], row["success"]) for row in first],
            [(row["failure_rate"], row["injection_draws"], row["success"]) for row in second],
        )

    def test_zero_failure_call_succeeds_on_first_attempt(self):
        record = simulate_one_call(
            rng=random.Random(4),
            failure_rate=0.0,
            call_id="zero-001",
            sleep=lambda _delay: None,
            attempt_work_seconds=0,
        )
        self.assertTrue(record["success"])
        self.assertEqual(record["attempts"], 1)


class AsyncRetryPolicyTests(unittest.IsolatedAsyncioTestCase):
    async def test_timeout_is_bounded_by_attempt_limit(self):
        calls = {"count": 0}

        async def slow_operation():
            calls["count"] += 1
            await asyncio.sleep(0.03)
            return "late"

        with self.assertRaises(TimeoutError):
            await retry_async(
                slow_operation,
                timeout_seconds=0.001,
                max_attempts=2,
                base_backoff_seconds=0,
                max_backoff_seconds=0,
                sleep=asyncio.sleep,
            )
        self.assertEqual(calls["count"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
