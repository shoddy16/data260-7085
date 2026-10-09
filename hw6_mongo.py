"""Lazy MongoDB access and schema initialization for HW6.

Importing this module never opens a network connection.  This keeps the
offline test suite independent from a running MongoDB service.
"""

from datetime import datetime, timezone
from typing import Any

from hw6_config import MONGO_DB, MONGO_URI

try:
    from pymongo import ASCENDING, DESCENDING, MongoClient
    from pymongo.errors import PyMongoError
except ImportError:  # pragma: no cover - dependency diagnostic
    ASCENDING = DESCENDING = None
    MongoClient = None
    PyMongoError = Exception

_client = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_client():
    global _client
    if MongoClient is None:
        raise RuntimeError("pymongo is required for live MongoDB operations")
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2500)
    return _client


def get_db():
    return get_client()[MONGO_DB]


def get_collection(name: str):
    return get_db()[name]


def ensure_hw6_schema() -> None:
    """Create collections/indexes and apply MongoDB document validation."""
    db = get_db()
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name", "status", "category", "inspectionDate", "createdAt", "updatedAt"],
            "properties": {
                "name": {"bsonType": "string", "minLength": 1, "maxLength": 100},
                "description": {"bsonType": ["string", "null"]},
                "status": {"enum": ["active", "needs_review", "closed"]},
                "category": {"enum": ["restaurant", "inspection", "facility"]},
                "inspectionDate": {"bsonType": "date"},
                "createdAt": {"bsonType": "date"},
                "updatedAt": {"bsonType": "date"},
            },
        }
    }
    if "domain_documents" not in db.list_collection_names():
        db.create_collection("domain_documents", validator=validator, validationLevel="strict")
    else:
        db.command("collMod", "domain_documents", validator=validator, validationLevel="strict")
    db.domain_documents.create_index([("createdAt", DESCENDING)])
    db.messages.create_index([("user_id", ASCENDING), ("session_id", ASCENDING), ("created_at", DESCENDING)])
    db.summaries.create_index([("user_id", ASCENDING), ("scope", ASCENDING), ("created_at", DESCENDING)])
    db.episodes.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])


def serialize_document(doc: dict[str, Any]) -> dict[str, Any]:
    result = dict(doc)
    if "_id" in result:
        result["id"] = str(result.pop("_id"))
    for key in ("inspectionDate", "createdAt", "updatedAt"):
        if isinstance(result.get(key), datetime):
            result[key] = result[key].isoformat()
    return result
