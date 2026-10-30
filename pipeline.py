"""Kafka-only three-stage agent pipeline with deterministic offline transport."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from hw8_config import DRAFTS, FINAL, INBOX, TASKS


@dataclass
class PipelineMessage:
    correlation_id: str
    payload: dict[str, Any]


class KafkaPipeline:
    def __init__(self):
        self.topics: dict[str, list[dict[str, Any]]] = {INBOX: [], TASKS: [], DRAFTS: [], FINAL: []}
        self.log: list[dict[str, Any]] = []

    def publish(self, topic: str, message: dict[str, Any]) -> None:
        self.topics[topic].append(deepcopy(message))
        self.log.append({"stage": "publish", "topic": topic, "message": deepcopy(message)})

    def run_once(self, question: str, correlation_id: str) -> dict[str, Any]:
        inbox = {"correlation_id": correlation_id, "question": question}
        self.publish(INBOX, inbox)
        task = {
            "correlation_id": correlation_id,
            "plan": ["search inspections", "summarize evidence"],
            "question": question,
        }
        self.publish(TASKS, task)
        draft = {"correlation_id": correlation_id, "answer": f"Inspection evidence for: {question}"}
        self.publish(DRAFTS, draft)
        final = {"correlation_id": correlation_id, "status": "approved", "answer": draft["answer"]}
        self.publish(FINAL, final)
        return final


def as_json(message: dict[str, Any]) -> str:
    return json.dumps(message, sort_keys=True)
