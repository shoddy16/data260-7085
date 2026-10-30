from __future__ import annotations

import json
import uuid
from collections import defaultdict, deque
from copy import deepcopy
from typing import Any

from hw8_config import ENTITY_RESPONSES


def new_correlation_id() -> str:
    return str(uuid.uuid4())


def validate_request(message: Any) -> str | None:
    if not isinstance(message, dict):
        return "message must be an object"
    for field in ("correlation_id", "reply_to", "operation", "data"):
        if field not in message:
            return f"{field} is required"
    if not isinstance(message["correlation_id"], str) or not message["correlation_id"].strip():
        return "correlation_id must be a non-empty string"
    if not isinstance(message["reply_to"], str) or not message["reply_to"].strip():
        return "reply_to must be a non-empty string"
    if not isinstance(message["data"], dict):
        return "data must be an object"
    return None


def inspection_payload(data: dict[str, Any]) -> str | None:
    for field in ("restaurantName", "location", "email", "description", "category"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            return f"{field} must be a non-empty string"
    score = data.get("score")
    if score is not None and (not isinstance(score, int) or not 0 <= score <= 100):
        return "score must be an integer between 0 and 100"
    return None


class EntityWorker:
    def __init__(self):
        self.entities: dict[str, dict[str, Any]] = {}
        self.processed: dict[str, dict[str, Any]] = {}
        self.side_effects = 0

    def process(self, request: dict[str, Any]) -> dict[str, Any]:
        correlation_id = request.get("correlation_id")
        if correlation_id in self.processed:
            return deepcopy(self.processed[correlation_id])
        error = validate_request(request)
        if error:
            result = {"success": False, "error": error}
        elif request["operation"] == "CREATE_ENTITY":
            error = inspection_payload(request["data"])
            if error:
                result = {"success": False, "error": error}
            else:
                entity_id = str(uuid.uuid4())
                self.entities[entity_id] = {"entity_id": entity_id, **deepcopy(request["data"])}
                self.side_effects += 1
                result = {"success": True, "entity_id": entity_id, "message": "Entity created"}
        elif request["operation"] == "GET_ENTITY":
            entity_id = request["data"].get("entity_id")
            result = (
                {"success": True, "entity": deepcopy(self.entities[entity_id])}
                if entity_id in self.entities
                else {"success": False, "error": "Entity not found"}
            )
        else:
            result = {"success": False, "error": "Unknown operation"}
        response = {"correlation_id": correlation_id, **result}
        if correlation_id:
            self.processed[correlation_id] = deepcopy(response)
        return response


class InMemoryBroker:
    def __init__(self):
        self.topics: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
        self.log: list[dict[str, Any]] = []

    def send(self, topic: str, message: dict[str, Any]) -> None:
        self.topics[topic].append(deepcopy(message))
        self.log.append({"event": "send", "topic": topic, "message": deepcopy(message)})

    def receive(self, topic: str) -> dict[str, Any]:
        message = self.topics[topic].popleft()
        self.log.append({"event": "receive", "topic": topic, "message": deepcopy(message)})
        return message


def encode(message: dict[str, Any]) -> bytes:
    return json.dumps(message, sort_keys=True).encode("utf-8")


def round_trip(worker: EntityWorker, payload: dict[str, Any]) -> dict[str, Any]:
    return worker.process({"correlation_id": new_correlation_id(), "reply_to": ENTITY_RESPONSES, **payload})
