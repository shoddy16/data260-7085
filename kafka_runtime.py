"""Optional real Kafka runtime. Importing this module does not require aiokafka."""

from __future__ import annotations

import asyncio
import json
import logging

from hw8_config import KAFKA_BOOTSTRAP_SERVERS
from kafka_protocol import EntityWorker

log = logging.getLogger(__name__)


async def run_entity_worker(bootstrap_servers: str = KAFKA_BOOTSTRAP_SERVERS) -> None:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

    from hw8_config import ENTITY_REQUESTS

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


async def run_stage(
    stage: str, input_topic: str, output_topic: str, bootstrap_servers: str = KAFKA_BOOTSTRAP_SERVERS
) -> None:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

    consumer = AIOKafkaConsumer(
        input_topic,
        bootstrap_servers=bootstrap_servers,
        group_id=f"s7085-{stage}",
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )
    producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
    await consumer.start()
    await producer.start()
    try:
        async for message in consumer:
            body = json.loads(message.value.decode("utf-8"))
            body["stage"] = stage
            await producer.send_and_wait(output_topic, json.dumps(body).encode("utf-8"))
            await consumer.commit()
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(run_entity_worker())
