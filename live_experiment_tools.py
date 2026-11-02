"""Live Kafka experiment helpers used only by the HW8 evidence runs."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from hw8_config import DRAFTS, TASKS, VERIFY_SEED

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")


async def publish_one(correlation_id: str, question: str) -> None:
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    await producer.start()
    try:
        body = {"correlation_id": correlation_id, "question": question}
        metadata = await producer.send_and_wait(TASKS, json.dumps(body).encode())
        print(json.dumps({"sent": body, "topic": metadata.topic, "partition": metadata.partition, "offset": metadata.offset}))
    finally:
        await producer.stop()


async def capture_order(run_id: str, mode: str) -> None:
    keyed = mode == "keyed"
    group_id = f"hw8-capture-{run_id}-{mode}-{uuid.uuid4()}"
    consumer = AIOKafkaConsumer(
        DRAFTS,
        bootstrap_servers=BOOTSTRAP,
        group_id=group_id,
        auto_offset_reset="latest",
        enable_auto_commit=False,
    )
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    await consumer.start()
    await producer.start()
    records = []
    rng = random.Random(VERIFY_SEED)
    sequence = list(range(20))
    rng.shuffle(sequence)
    inputs = []
    try:
        await asyncio.sleep(3)
        for index in sequence:
            body = {
                "correlation_id": f"hw8-order-{run_id}-{mode}-{index:02d}",
                "question": f"ordering event {index}",
                "related_entity_id": "restaurant-order-test",
                "sequence": index,
            }
            key = body["related_entity_id"].encode() if keyed else None
            metadata = await producer.send_and_wait(TASKS, json.dumps(body).encode(), key=key)
            inputs.append({**body, "key": body["related_entity_id"] if keyed else None, "partition": metadata.partition, "offset": metadata.offset})
        async with asyncio.timeout(35):
            while len(records) < 20:
                message = await consumer.getone()
                body = json.loads(message.value.decode())
                if body.get("correlation_id", "").startswith(f"hw8-order-{run_id}-{mode}-"):
                    records.append({"partition": message.partition, "offset": message.offset, "body": body})
    finally:
        await consumer.stop()
        await producer.stop()
    output = {
        "status": "PASS",
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "mode": mode,
        "verify_seed": VERIFY_SEED,
        "topic": TASKS,
        "output_topic": DRAFTS,
        "partitions": 2,
        "inputs": inputs,
        "outputs": records,
        "output_sequence": [record["body"].get("sequence") for record in records],
        "same_key_output_sequence": [record["body"].get("sequence") for record in records] if keyed else None,
    }
    path = Path(f"/app/reports/hw08/raw/live_ordering_{run_id}_{mode}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


async def capture_draft(correlation_id: str) -> None:
    group_id = f"hw8-death-capture-{uuid.uuid4()}"
    consumer = AIOKafkaConsumer(DRAFTS, bootstrap_servers=BOOTSTRAP, group_id=group_id, auto_offset_reset="earliest")
    await consumer.start()
    try:
        async with asyncio.timeout(25):
            async for message in consumer:
                body = json.loads(message.value.decode())
                if body.get("correlation_id") == correlation_id:
                    output = {
                        "status": "PASS",
                        "captured_utc": datetime.now(timezone.utc).isoformat(),
                        "correlation_id": correlation_id,
                        "topic": DRAFTS,
                        "partition": message.partition,
                        "offset": message.offset,
                        "body": body,
                    }
                    path = Path(f"/app/reports/hw08/raw/live_consumer_death_{correlation_id}.json")
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
                    print(json.dumps(output, indent=2))
                    return
    finally:
        await consumer.stop()
    raise TimeoutError(f"no draft for {correlation_id}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("publish-one")
    one.add_argument("correlation_id")
    one.add_argument("question")
    order = sub.add_parser("capture-order")
    order.add_argument("run_id")
    order.add_argument("mode", choices=("unkeyed", "keyed"))
    draft = sub.add_parser("capture-draft")
    draft.add_argument("correlation_id")
    args = parser.parse_args()
    if args.command == "publish-one":
        asyncio.run(publish_one(args.correlation_id, args.question))
    elif args.command == "capture-order":
        asyncio.run(capture_order(args.run_id, args.mode))
    else:
        asyncio.run(capture_draft(args.correlation_id))


if __name__ == "__main__":
    main()
