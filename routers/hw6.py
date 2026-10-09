"""HW6 MongoDB document and memory endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from hw6_memory import ChatRequest, DocumentCreate, DocumentUpdate, VALID_CATEGORY, VALID_STATUS, chat_turn
from hw6_mongo import ensure_hw6_schema, get_collection, serialize_document

router = APIRouter(prefix="/api", tags=["HW6 MongoDB and memory"])


def _live_collection():
    try:
        ensure_hw6_schema()
        return get_collection("domain_documents")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB unavailable: {type(exc).__name__}") from exc


def _validate_categories(payload):
    if payload.status is not None and payload.status not in VALID_STATUS:
        raise HTTPException(status_code=422, detail="status must be active, needs_review, or closed")
    if payload.category is not None and payload.category not in VALID_CATEGORY:
        raise HTTPException(status_code=422, detail="category must be restaurant, inspection, or facility")


@router.post("/documents", status_code=status.HTTP_201_CREATED)
def create_document(payload: DocumentCreate):
    _validate_categories(payload)
    collection = _live_collection()
    now = datetime.now(timezone.utc)
    doc = payload.model_dump()
    doc.update({"createdAt": now, "updatedAt": now})
    try:
        result = collection.insert_one(doc)
        return serialize_document(collection.find_one({"_id": result.inserted_id}))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to create document: {type(exc).__name__}") from exc


@router.get("/documents")
def list_documents():
    collection = _live_collection()
    try:
        return [serialize_document(doc) for doc in collection.find().sort("createdAt", -1)]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to list documents: {type(exc).__name__}") from exc


def _object_id(value: str):
    try:
        from bson import ObjectId
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid document id") from exc


@router.get("/documents/{document_id}")
def get_document(document_id: str):
    collection = _live_collection()
    doc = collection.find_one({"_id": _object_id(document_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return serialize_document(doc)


@router.put("/documents/{document_id}")
def update_document(document_id: str, payload: DocumentUpdate):
    _validate_categories(payload)
    collection = _live_collection()
    oid = _object_id(document_id)
    if not collection.find_one({"_id": oid}):
        raise HTTPException(status_code=404, detail="Document not found")
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="At least one field is required")
    updates["updatedAt"] = datetime.now(timezone.utc)
    collection.update_one({"_id": oid}, {"$set": updates})
    return serialize_document(collection.find_one({"_id": oid}))


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str):
    collection = _live_collection()
    result = collection.delete_one({"_id": _object_id(document_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")


@router.post("/chat")
def chat(payload: ChatRequest):
    try:
        return chat_turn(payload)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chat request failed: {type(exc).__name__}") from exc


def _json_safe(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items() if key != "_id"}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


@router.get("/memory/{user_id}")
def memory(user_id: str):
    try:
        from hw6_memory import MongoMemoryStore
        store = MongoMemoryStore()
        messages = store.messages(user_id)[-16:]
        sessions = store.summaries(user_id, "session")
        lifetime = store.summaries(user_id, "user")
        return _json_safe({"messages": messages, "latest_session_summary": sessions[0] if sessions else None, "latest_lifetime_summary": lifetime[0] if lifetime else None, "episodes": store.episodes(user_id)[-20:]})
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB unavailable: {type(exc).__name__}") from exc


@router.get("/aggregate/{user_id}")
def aggregate(user_id: str):
    try:
        from collections import Counter
        from hw6_memory import MongoMemoryStore
        store = MongoMemoryStore()
        counts = Counter(item.get("created_at").date().isoformat() for item in store.messages(user_id) if hasattr(item.get("created_at"), "date"))
        summaries = store.summaries(user_id)[:5]
        return {"daily_message_counts": dict(sorted(counts.items())), "recent_summaries": _json_safe(summaries)}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB unavailable: {type(exc).__name__}") from exc
