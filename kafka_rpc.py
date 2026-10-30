"""FastAPI-facing Kafka request/response wrapper with an offline fallback."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from hw8_config import ENTITY_REQUESTS, ENTITY_RESPONSES
from kafka_protocol import EntityWorker, new_correlation_id


class KafkaRPC:
    def __init__(self, worker: EntityWorker | None = None):
        self.worker = worker or EntityWorker()
        self.live = os.getenv("HW8_LIVE_KAFKA", "0") == "1"

    async def request(self, operation: str, data: dict[str, Any]) -> dict[str, Any]:
        correlation_id = new_correlation_id()
        request = {
            "correlation_id": correlation_id,
            "reply_to": ENTITY_RESPONSES,
            "operation": operation,
            "data": data,
        }
        if self.live:
            return await self._request_live(request)
        response = self.worker.process(request)
        response["request_topic"] = ENTITY_REQUESTS
        response["response_topic"] = ENTITY_RESPONSES
        return response

    async def _request_live(self, request: dict[str, Any]) -> dict[str, Any]:
        from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

        from hw8_config import KAFKA_BOOTSTRAP_SERVERS

        consumer = AIOKafkaConsumer(
            ENTITY_RESPONSES,
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", KAFKA_BOOTSTRAP_SERVERS),
            group_id=f"s7085-api-{request['correlation_id']}",
            auto_offset_reset="latest",
            enable_auto_commit=False,
        )
        producer = AIOKafkaProducer(bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", KAFKA_BOOTSTRAP_SERVERS))
        await consumer.start()
        await producer.start()
        try:
            await producer.send_and_wait(ENTITY_REQUESTS, json.dumps(request).encode("utf-8"))
            async for message in consumer:
                response = json.loads(message.value.decode("utf-8"))
                if response.get("correlation_id") == request["correlation_id"]:
                    await consumer.commit()
                    response["request_topic"] = ENTITY_REQUESTS
                    response["response_topic"] = ENTITY_RESPONSES
                    return response
        finally:
            await consumer.stop()
            await producer.stop()
        raise asyncio.TimeoutError(f"No response for {request['correlation_id']}")
