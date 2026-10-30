"""FastAPI-facing Kafka request/response wrapper with an offline fallback."""

from __future__ import annotations

from typing import Any

from hw8_config import ENTITY_REQUESTS, ENTITY_RESPONSES
from kafka_protocol import EntityWorker, new_correlation_id


class KafkaRPC:
    def __init__(self, worker: EntityWorker | None = None):
        self.worker = worker or EntityWorker()

    async def request(self, operation: str, data: dict[str, Any]) -> dict[str, Any]:
        correlation_id = new_correlation_id()
        request = {
            "correlation_id": correlation_id,
            "reply_to": ENTITY_RESPONSES,
            "operation": operation,
            "data": data,
        }
        response = self.worker.process(request)
        response["request_topic"] = ENTITY_REQUESTS
        response["response_topic"] = ENTITY_RESPONSES
        return response
