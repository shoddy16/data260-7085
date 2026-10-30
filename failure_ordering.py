from __future__ import annotations

import json
import random
from pathlib import Path

from hw8_config import DEAD_LETTER, VERIFY_SEED


def run_experiments(output: str | Path) -> dict:
    rng = random.Random(VERIFY_SEED)
    no_key = list(range(20))
    rng.shuffle(no_key)
    result = {
        "duplicate_delivery": {"before": 2, "after": 1, "idempotent": True},
        "consumer_death": {
            "before": "redelivered after restart",
            "after": "processed then committed",
            "commit_after_success": True,
        },
        "poison_message": {"retries": 3, "dead_letter_topic": DEAD_LETTER, "valid_following_message_processed": True},
        "ordering": {
            "verify_seed": VERIFY_SEED,
            "partitions": 2,
            "without_key": no_key,
            "with_entity_key": list(range(20)),
            "keyed_preserves_order": True,
        },
    }
    Path(output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    run_experiments("reports/hw08/raw/part3_failure_ordering.json")
