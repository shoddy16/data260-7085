"""Run and capture one real Kafka pipeline journey inside the API image."""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from hw8_config import DRAFTS, FINAL, INBOX, TASKS


async def read_match(topic: str, correlation_id: str, group_id: str) -> dict:
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )
    await consumer.start()
    try:
        async with asyncio.timeout(20):
            async for message in consumer:
                body = json.loads(message.value.decode("utf-8"))
                if body.get("correlation_id") == correlation_id:
                    return {"topic": topic, "partition": message.partition, "offset": message.offset, "body": body}
    finally:
        await consumer.stop()
    raise TimeoutError(f"no matching message on {topic}")


async def main() -> None:
    correlation_id = f"live-{uuid.uuid4()}"
    producer = AIOKafkaProducer(bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"))
    await producer.start()
    try:
        await producer.send_and_wait(INBOX, json.dumps({"correlation_id": correlation_id, "question": "Which restaurant inspections scored below 70?"}).encode())
    finally:
        await producer.stop()
    records = {}
    for name, topic in (("task", TASKS), ("draft", DRAFTS), ("final", FINAL)):
        records[name] = await read_match(topic, correlation_id, f"hw8-capture-{name}-{uuid.uuid4()}")
    result = {"captured_utc": datetime.now(timezone.utc).isoformat(), "correlation_id": correlation_id, "records": records}
    path = Path("/app/reports/hw08/evidence/live_pipeline.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
