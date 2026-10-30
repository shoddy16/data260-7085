import json
from pathlib import Path

from failure_ordering import run_experiments
from hw8_config import DEAD_LETTER, ENTITY_RESPONSES, PREFIX
from kafka_protocol import EntityWorker, validate_request
from pipeline import KafkaPipeline


def data():
    return {
        "restaurantName": "Test Restaurant",
        "location": "San Jose",
        "email": "test@example.com",
        "description": "routine",
        "category": "restaurant",
        "score": 88,
    }


def test_round_trip_and_correlation():
    worker = EntityWorker()
    cid = "same-correlation"
    created = worker.process(
        {"correlation_id": cid, "reply_to": ENTITY_RESPONSES, "operation": "CREATE_ENTITY", "data": data()}
    )
    fetched = worker.process(
        {
            "correlation_id": "get",
            "reply_to": ENTITY_RESPONSES,
            "operation": "GET_ENTITY",
            "data": {"entity_id": created["entity_id"]},
        }
    )
    assert (
        created["success"]
        and created["correlation_id"] == cid
        and fetched["entity"]["entity_id"] == created["entity_id"]
    )
    assert PREFIX == "s7085"


def test_validation_and_errors_preserve_correlation():
    worker = EntityWorker()
    base = {"reply_to": ENTITY_RESPONSES, "data": {}}
    assert validate_request({}) == "correlation_id is required"
    assert worker.process({**base, "correlation_id": "unknown", "operation": "NOPE"})["error"] == "Unknown operation"
    assert (
        worker.process({**base, "correlation_id": "invalid", "operation": "CREATE_ENTITY"})["error"]
        == "restaurantName must be a non-empty string"
    )
    assert (
        worker.process({**base, "correlation_id": "missing", "operation": "GET_ENTITY"})["correlation_id"] == "missing"
    )


def test_duplicate_delivery_has_no_extra_side_effect():
    worker = EntityWorker()
    msg = {"correlation_id": "dup", "reply_to": ENTITY_RESPONSES, "operation": "CREATE_ENTITY", "data": data()}
    first = worker.process(msg)
    second = worker.process(msg)
    assert first == second and worker.side_effects == 1


def test_pipeline_final_json():
    assert KafkaPipeline().run_once("question", "cid-1")["status"] == "approved"


def test_failure_ordering_artifact():
    output = Path("reports/hw08/raw/test_failure_ordering.json")
    result = run_experiments(output)
    assert result["poison_message"]["dead_letter_topic"] == DEAD_LETTER
    assert result["ordering"]["keyed_preserves_order"]
    assert json.loads(output.read_text())["duplicate_delivery"]["idempotent"]
