"""Optional real Kafka runtime. Importing this module does not require aiokafka."""

from __future__ import annotations

import asyncio
import json
import logging
import os

from hw8_config import DEAD_LETTER, KAFKA_BOOTSTRAP_SERVERS
from kafka_protocol import EntityWorker

log = logging.getLogger(__name__)
MAX_RETRIES = 3


def transform(stage: str, body: dict) -> dict:
    correlation_id = body.get("correlation_id")
    if stage == "planner":
        return {
            "correlation_id": correlation_id,
            "question": body.get("question", ""),
            "plan": ["search inspections", "summarize evidence"],
        }
    if stage == "writer":
        return {
            "correlation_id": correlation_id,
            "question": body.get("question", ""),
            "draft": f"Inspection evidence for: {body.get('question', '')}",
        }
    if stage == "reviewer":
        return {"correlation_id": correlation_id, "status": "approved", "answer": body.get("draft", "")}
    raise ValueError(f"unknown stage: {stage}")


async def run_entity_worker(bootstrap_servers: str | None = None) -> None:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

    from hw8_config import ENTITY_REQUESTS

    bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", KAFKA_BOOTSTRAP_SERVERS)
    worker = EntityWorker()
    consumer = AIOKafkaConsumer(
        ENTITY_REQUESTS,
        bootstrap_servers=bootstrap_servers,
        group_id="s7085-entity-worker",
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )
    producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
    await consumer.start()
    await producer.start()
    log.info("Consumer is ready and listening... topic=%s", ENTITY_REQUESTS)
    try:
        async for message in consumer:
            request = json.loads(message.value.decode("utf-8"))
            response = worker.process(request)
            await producer.send_and_wait(request.get("reply_to"), json.dumps(response).encode("utf-8"))
            await consumer.commit()
    finally:
        await consumer.stop()
        await producer.stop()


async def run_stage(stage: str, input_topic: str, output_topic: str, bootstrap_servers: str | None = None) -> None:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

    bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", KAFKA_BOOTSTRAP_SERVERS)
    consumer = AIOKafkaConsumer(
        input_topic,
        bootstrap_servers=bootstrap_servers,
        group_id=os.getenv("KAFKA_GROUP_ID", f"s7085-{stage}"),
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )
    producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
    await consumer.start()
    await producer.start()
    try:
        async for message in consumer:
            raw = json.loads(message.value.decode("utf-8"))
            correlation_id = raw.get("correlation_id")
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    body = transform(stage, raw)
                    body["stage"] = stage
                    key = raw.get("related_entity_id") if stage == "planner" else None
                    await producer.send_and_wait(
                        output_topic, json.dumps(body).encode("utf-8"), key=key.encode("utf-8") if key else None
                    )
                    log.info(
                        "%s correlation_id=%s attempt=%s in=%s out=%s",
                        stage,
                        correlation_id,
                        attempt,
                        input_topic,
                        output_topic,
                    )
                    await consumer.commit()
                    break
                except Exception as error:
                    log.warning("%s retry correlation_id=%s attempt=%s error=%s", stage, correlation_id, attempt, error)
                    if attempt == MAX_RETRIES:
                        dead = {
                            "correlation_id": correlation_id,
                            "error": str(error),
                            "attempts": attempt,
                            "original": raw,
                        }
                        await producer.send_and_wait(DEAD_LETTER, json.dumps(dead).encode("utf-8"))
                        await consumer.commit()
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(run_entity_worker())
