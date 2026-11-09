"""HW9 cache and self-improvement endpoints."""

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import get_db
from hw9_agents import SelfImprovingSystem
from hw9_cache import EmbeddingProvider, SemanticCache, ViewCounter
from jwt_auth import get_current_user

router = APIRouter(prefix="/hw9", tags=["hw9"])


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    restaurant_id: int | None = Field(default=None, gt=0)


class AskResponse(BaseModel):
    answer: str
    is_cached: bool
    similarity: float
    lookup_latency_ms: float
    agent_latency_ms: float
    total_latency_ms: float
    agent_executed: bool


class ViewResponse(BaseModel):
    restaurant_id: int
    views: int


class MemoryRedis:
    def __init__(self):
        self.values: dict[str, str] = {}
        self.sets: dict[str, set[str]] = {}

    def incr(self, key):
        value = int(self.values.get(key, "0")) + 1
        self.values[key] = str(value)
        return value

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def smembers(self, key):
        return self.sets.get(key, set())

    def delete(self, key):
        self.values.pop(key, None)
        self.sets.pop(key, None)
        return 1

    def ft(self, _name):
        raise RuntimeError("local fallback has no vector index")


try:
    import redis

    redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    redis_client.ping()
except Exception:
    redis_client = MemoryRedis()

semantic_cache = SemanticCache(redis_client, provider=EmbeddingProvider())
REFERENCE = Path(__file__).resolve().parent.parent / "data" / "hw9" / "reference_data.json"
LESSONS = Path(__file__).resolve().parent.parent / "data" / "hw9" / "lessons.json"
try:
    from src.model_client import ModelClient

    model_client = ModelClient()
except Exception:
    model_client = None
system = SelfImprovingSystem(REFERENCE, LESSONS, model_client=model_client)


def query_signature(question: str) -> str:
    words = question.lower().split()
    if "below" in words or "under" in words:
        return "score_below"
    if "above" in words or "over" in words:
        return "score_above"
    return "general"


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    def run_agent_once() -> str:
        result = system.run(payload.question)
        return result.get("revised_answer") or result["initial_answer"]

    result = semantic_cache.answer(
        payload.question,
        query_signature(payload.question),
        run_agent_once,
        payload.restaurant_id,
    )
    return AskResponse(**result.__dict__)


@router.post("/restaurants/{restaurant_id}/views", response_model=ViewResponse)
def increment_views(
    restaurant_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    try:
        views = ViewCounter(redis_client).increment_restaurant_views(restaurant_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ViewResponse(restaurant_id=restaurant_id, views=views)


@router.get("/health")
def health():
    return {"status": "ok", "redis_backend": type(redis_client).__name__}
