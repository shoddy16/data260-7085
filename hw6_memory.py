"""MongoDB-backed short-, long-, and episodic-memory implementation."""

from __future__ import annotations

import math
import re
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Protocol

from pydantic import BaseModel, Field

from hw6_config import EPISODIC_TOP_K, OLLAMA_MODEL, OLLAMA_URL, SHORT_TERM_N, SUMMARIZE_EVERY_USER_MSGS
from hw6_mongo import get_collection, get_db, utc_now


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    session_id: str | None = Field(default=None, max_length=100)
    message: str = Field(min_length=1, max_length=4000)


class DocumentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    status: str = "active"
    category: str = "restaurant"
    inspectionDate: datetime


class DocumentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    status: str | None = None
    category: str | None = None
    inspectionDate: datetime | None = None


VALID_STATUS = {"active", "needs_review", "closed"}
VALID_CATEGORY = {"restaurant", "inspection", "facility"}


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text or "") / 4))


def tokenize(text: str) -> Counter[str]:
    return Counter(re.findall(r"[a-z0-9]+", (text or "").lower()))


def local_embedding(text: str, dimensions: int = 64) -> list[float]:
    """Deterministic local embedding used for reproducible offline runs."""
    vector = [0.0] * dimensions
    import hashlib
    for token, count in tokenize(text).items():
        bucket = int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:4], "big") % dimensions
        vector[bucket] += float(count)
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    return sum(left[i] * right[i] for i in range(size))


class ChatModel(Protocol):
    def complete(self, prompt: str) -> tuple[str, dict[str, int]]: ...


class OllamaChatModel:
    def __init__(self, model: str = OLLAMA_MODEL, base_url: str = OLLAMA_URL):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def complete(self, prompt: str) -> tuple[str, dict[str, int]]:
        import httpx
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False, "options": {"temperature": 0, "num_predict": 16}},
            timeout=120,
        )
        response.raise_for_status()
        body = response.json()
        usage = {
            "prompt_tokens": int(body.get("prompt_eval_count") or estimate_tokens(prompt)),
            "completion_tokens": int(body.get("eval_count") or estimate_tokens(body.get("response", ""))),
        }
        return str(body.get("response", "")), usage


class DeterministicChatModel:
    """Offline model for tests and reproducible cost experiments."""

    def complete(self, prompt: str) -> tuple[str, dict[str, int]]:
        answer = "I used the available inspection memory and will keep this fact for later turns."
        return answer, {"prompt_tokens": estimate_tokens(prompt), "completion_tokens": estimate_tokens(answer)}


class MemoryStore(Protocol):
    def add_message(self, doc: dict[str, Any]) -> None: ...
    def add_summary(self, doc: dict[str, Any]) -> None: ...
    def add_episode(self, doc: dict[str, Any]) -> None: ...
    def messages(self, user_id: str, session_id: str | None = None) -> list[dict[str, Any]]: ...
    def summaries(self, user_id: str, scope: str | None = None) -> list[dict[str, Any]]: ...
    def episodes(self, user_id: str) -> list[dict[str, Any]]: ...


class MongoMemoryStore:
    def add_message(self, doc): get_collection("messages").insert_one(doc)
    def add_summary(self, doc): get_collection("summaries").insert_one(doc)
    def add_episode(self, doc): get_collection("episodes").insert_one(doc)

    def messages(self, user_id, session_id=None):
        query = {"user_id": user_id}
        if session_id is not None: query["session_id"] = session_id
        return list(get_collection("messages").find(query).sort("created_at", 1))

    def summaries(self, user_id, scope=None):
        query = {"user_id": user_id}
        if scope is not None: query["scope"] = scope
        return list(get_collection("summaries").find(query).sort("created_at", -1))

    def episodes(self, user_id):
        return list(get_collection("episodes").find({"user_id": user_id}).sort("created_at", -1))


class InMemoryStore:
    def __init__(self): self.data = {"messages": [], "summaries": [], "episodes": []}
    def add_message(self, doc): self.data["messages"].append(dict(doc))
    def add_summary(self, doc): self.data["summaries"].append(dict(doc))
    def add_episode(self, doc): self.data["episodes"].append(dict(doc))
    def messages(self, user_id, session_id=None):
        return [x for x in self.data["messages"] if x["user_id"] == user_id and (session_id is None or x.get("session_id") == session_id)]
    def summaries(self, user_id, scope=None):
        rows = [x for x in self.data["summaries"] if x["user_id"] == user_id and (scope is None or x.get("scope") == scope)]
        return list(reversed(rows))
    def episodes(self, user_id): return [x for x in self.data["episodes"] if x["user_id"] == user_id]


def _fact_from_message(message: str) -> tuple[str, float] | None:
    cleaned = " ".join(message.split())
    if not cleaned: return None
    return cleaned[:160], min(1.0, max(0.1, len(tokenize(cleaned)) / 20))


def summarize(messages: list[dict[str, Any]]) -> str:
    lines = []
    for item in messages[-10:]:
        lines.append(f"- {item.get('role')}: {str(item.get('content', '')).strip()[:180]}")
    return "Conversation highlights:\n" + "\n".join(lines)


def assemble_prompt(user_message: str, session_summary: str, lifetime_summary: str, recent: list[dict[str, Any]], episodes: list[dict[str, Any]], file_memory: str = "") -> str:
    short = "\n".join(f"{m.get('role')}: {m.get('content')}" for m in recent)
    facts = "\n".join(f"- {e.get('fact')}" for e in episodes)
    return ("You are a careful restaurant-inspection assistant.\n" + file_memory +
            f"\nLifetime summary:\n{lifetime_summary or '(none)'}\nSession summary:\n{session_summary or '(none)'}\n"+
            f"Short-term window:\n{short or '(none)'}\nEpisodic facts:\n{facts or '(none)'}\nCurrent user message: {user_message}\nAssistant:")


def retrieve_episodes(store: MemoryStore, user_id: str, message: str, top_k: int = EPISODIC_TOP_K) -> list[dict[str, Any]]:
    query = local_embedding(message)
    scored = [(cosine_similarity(query, item.get("embedding", [])), item) for item in store.episodes(user_id)]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [dict(item, similarity=round(score, 4)) for score, item in scored[:top_k]]


def chat_turn(request: ChatRequest, store: MemoryStore | None = None, model: ChatModel | None = None, short_term_n: int = SHORT_TERM_N, summarize_every: int = SUMMARIZE_EVERY_USER_MSGS) -> dict[str, Any]:
    store = store or MongoMemoryStore()
    model = model or OllamaChatModel()
    now = utc_now()
    session_id = request.session_id or "default"
    user_doc = {"user_id": request.user_id, "session_id": session_id, "role": "user", "content": request.message, "created_at": now}
    store.add_message(user_doc)
    all_messages = store.messages(request.user_id, session_id)
    recent = all_messages[-short_term_n:]
    session_summary = (store.summaries(request.user_id, "session") or [{}])[0].get("text", "")
    lifetime_summary = (store.summaries(request.user_id, "user") or [{}])[0].get("text", "")
    episodes = retrieve_episodes(store, request.user_id, request.message)
    prompt = assemble_prompt(request.message, session_summary, lifetime_summary, recent, episodes)
    started = time.perf_counter()
    reply, usage = model.complete(prompt)
    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    store.add_message({"user_id": request.user_id, "session_id": session_id, "role": "assistant", "content": reply, "created_at": utc_now()})
    user_count = sum(1 for item in all_messages if item.get("role") == "user")
    if user_count % summarize_every == 0:
        store.add_summary({"user_id": request.user_id, "session_id": session_id, "scope": "session", "text": summarize(all_messages), "created_at": utc_now()})
        session_summaries = store.summaries(request.user_id, "session")
        if len(session_summaries) >= 2:
            store.add_summary({"user_id": request.user_id, "session_id": None, "scope": "user", "text": summarize(session_summaries), "created_at": utc_now()})
    fact = _fact_from_message(request.message)
    if fact:
        text, importance = fact
        store.add_episode({"user_id": request.user_id, "session_id": session_id, "fact": text, "importance": importance, "embedding": local_embedding(text), "created_at": utc_now()})
    metrics = {"prompt_tokens": usage.get("prompt_tokens", estimate_tokens(prompt)), "completion_tokens": usage.get("completion_tokens", estimate_tokens(reply)), "system_tokens": estimate_tokens("You are a careful restaurant-inspection assistant."), "long_term_tokens": estimate_tokens(session_summary + lifetime_summary), "short_term_tokens": estimate_tokens("\n".join(str(x.get("content", "")) for x in recent)), "episodic_tokens": estimate_tokens("\n".join(str(x.get("fact", "")) for x in episodes)), "latency_ms": latency_ms}
    return {"reply": reply, "used": {"short_term": recent, "long_term_summary": session_summary or lifetime_summary or None, "episodic_facts": episodes}, "metrics": metrics}
