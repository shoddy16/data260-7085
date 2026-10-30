"""Offline-complete RPC demonstration; use KAFKA_LIVE=1 for the Docker adapter."""

import asyncio
import json
import logging
import os

from hw8_config import ENTITY_REQUESTS, ENTITY_RESPONSES
from kafka_protocol import EntityWorker, new_correlation_id
from kafka_rpc import KafkaRPC

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("homework_demo")


async def main():
    if os.getenv("HW8_LIVE_KAFKA") == "1":
        rpc = KafkaRPC()
        created = await rpc.request(
            "CREATE_ENTITY",
            {
                "restaurantName": "Demo Cafe",
                "location": "San Jose",
                "email": "demo@example.com",
                "description": "Routine inspection",
                "category": "restaurant",
                "score": 94,
            },
        )
        log.info("CLIENT live CREATE response=%s", json.dumps(created))
        retrieved = await rpc.request("GET_ENTITY", {"entity_id": created["entity_id"]})
        log.info("CLIENT live GET response=%s", json.dumps(retrieved))
        return {"create": created, "get": retrieved}
    worker = EntityWorker()
    correlation_id = new_correlation_id()
    create = {
        "correlation_id": correlation_id,
        "reply_to": ENTITY_RESPONSES,
        "operation": "CREATE_ENTITY",
        "data": {
            "restaurantName": "Demo Cafe",
            "location": "San Jose",
            "email": "demo@example.com",
            "description": "Routine inspection",
            "category": "restaurant",
            "score": 94,
        },
    }
    log.info("CLIENT send topic=%s message=%s", ENTITY_REQUESTS, json.dumps(create))
    log.info("WORKER receive/process correlation_id=%s", correlation_id)
    created = worker.process(create)
    log.info("WORKER reply topic=%s response=%s", ENTITY_RESPONSES, json.dumps(created))
    log.info("CLIENT response correlation_id=%s entity_id=%s", created["correlation_id"], created["entity_id"])
    get = {
        "correlation_id": correlation_id,
        "reply_to": ENTITY_RESPONSES,
        "operation": "GET_ENTITY",
        "data": {"entity_id": created["entity_id"]},
    }
    log.info("CLIENT send topic=%s message=%s", ENTITY_REQUESTS, json.dumps(get))
    retrieved = worker.process(get)
    log.info("WORKER reply topic=%s response=%s", ENTITY_RESPONSES, json.dumps(retrieved))
    log.info(
        "CLIENT response correlation_id=%s entity=%s", retrieved["correlation_id"], json.dumps(retrieved["entity"])
    )
    assert retrieved["correlation_id"] == correlation_id
    return {"create": created, "get": retrieved}


if __name__ == "__main__":
    asyncio.run(main())
