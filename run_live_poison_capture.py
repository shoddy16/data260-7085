"""Exercise the live Writer retry/dead-letter path with Kafka."""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from hw8_config import DEAD_LETTER, DRAFTS, TASKS


async def wait_for(topic: str, correlation_id: str, group_id: str) -> dict:
    consumer = AIOKafkaConsumer(topic, bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"), group_id=group_id, auto_offset_reset="earliest")
    await consumer.start()
    try:
        async with asyncio.timeout(25):
            async for message in consumer:
                body = json.loads(message.value.decode())
                if body.get("correlation_id") == correlation_id:
                    return {"topic": topic, "partition": message.partition, "offset": message.offset, "body": body}
    finally:
        await consumer.stop()
    raise TimeoutError(f"no {correlation_id} on {topic}")


async def main() -> None:
    poison_id = f"poison-{uuid.uuid4()}"
    valid_id = f"valid-after-poison-{uuid.uuid4()}"
    poison_wait = asyncio.create_task(wait_for(DEAD_LETTER, poison_id, f"hw8-poison-{uuid.uuid4()}"))
    valid_wait = asyncio.create_task(wait_for(DRAFTS, valid_id, f"hw8-valid-{uuid.uuid4()}"))
    await asyncio.sleep(4)
    producer = AIOKafkaProducer(bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"))
    await producer.start()
    try:
        await producer.send_and_wait(TASKS, json.dumps({"correlation_id": poison_id, "poison": True}).encode())
        await producer.send_and_wait(TASKS, json.dumps({"correlation_id": valid_id, "question": "valid after poison"}).encode())
    finally:
        await producer.stop()
    poison, valid = await asyncio.gather(poison_wait, valid_wait)
    result = {"captured_utc": datetime.now(timezone.utc).isoformat(), "poison": poison, "valid_after_poison": valid}
    path = Path("/app/reports/hw08/evidence/live_poison.json")
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
