"""Redis-backed view counter and semantic cache for HW9."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import struct
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable

from hw9_config import (
    CACHE_KEY,
    DATA_VERSION_KEY,
    DEFAULT_THRESHOLD,
    EMBEDDING_DIM,
    EMBEDDING_MODEL,
    PREFIX,
    VIEW_KEY,
)

log = logging.getLogger(__name__)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    return dot / (norm_left * norm_right) if norm_left and norm_right else 0.0


class ViewCounter:
    """Increment Redis on every access and persist every tenth count."""

    def __init__(self, redis_client: Any):
        self.redis = redis_client

    def increment_restaurant_views(self, restaurant_id: int, db: Any) -> int:
        key = f"{VIEW_KEY}:{restaurant_id}"
        try:
            count = int(self.redis.incr(key))
        except Exception as exc:
            log.exception("Redis view increment failed for restaurant %s", restaurant_id)
            raise RuntimeError("Unable to increment restaurant views") from exc
        if count % 10 == 0:
            restaurant = db.query(RestaurantModel).filter(RestaurantModel.id == restaurant_id).first()
            if restaurant is None:
                raise ValueError(f"Restaurant {restaurant_id} not found")
            restaurant.views = count
            try:
                db.commit()
                log.info("Synced views to database restaurant_id=%s count=%s", restaurant_id, count)
            except Exception:
                db.rollback()
                log.exception("View database sync failed restaurant_id=%s count=%s", restaurant_id, count)
                raise
        return count


try:
    from models.models import Restaurant as RestaurantModel
except ImportError:  # pragma: no cover - allows isolated utility tests
    RestaurantModel = None


class EmbeddingProvider:
    """Use a local Ollama embedding endpoint, with deterministic offline fallback."""

    def __init__(self, embedder: Callable[[str], list[float]] | None = None, model: str = EMBEDDING_MODEL):
        self._embedder = embedder
        self.model = model
        self._ollama_unavailable = False
        self._embeddings: dict[str, list[float]] = {}
        self.base_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")

    def embed(self, text: str) -> list[float]:
        if text in self._embeddings:
            return self._embeddings[text]
        if self._embedder:
            embedding = self._embedder(text)
            self._embeddings[text] = embedding
            return embedding
        try:
            if self._ollama_unavailable:
                raise RuntimeError("previous Ollama embedding attempt failed")
            import httpx

            response = httpx.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=float(os.getenv("OLLAMA_EMBEDDING_TIMEOUT", "30")),
            )
            response.raise_for_status()
            embedding = response.json().get("embedding")
            if embedding:
                result = [float(value) for value in embedding]
                self._embeddings[text] = result
                return result
        except Exception:
            self._ollama_unavailable = True
            log.debug("Ollama embeddings unavailable; using deterministic fallback", exc_info=True)
        # Deterministic fallback keeps experiments reproducible when Ollama is unavailable.
        vector = [0.0] * EMBEDDING_DIM
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode()).digest()
            for index in (digest[0] % EMBEDDING_DIM, digest[1] % EMBEDDING_DIM, digest[2] % EMBEDDING_DIM):
                vector[index] += 1.0
        self._embeddings[text] = vector
        return vector


@dataclass
class CacheResult:
    answer: str | None
    is_cached: bool
    similarity: float
    lookup_latency_ms: float
    agent_latency_ms: float
    total_latency_ms: float
    agent_executed: bool
    cache_id: str | None = None


class SemanticCache:
    """Semantic cache with Redis HNSW KNN lookup and version checks."""

    def __init__(
        self,
        redis_client: Any,
        threshold: float = DEFAULT_THRESHOLD,
        provider: EmbeddingProvider | None = None,
        index_name: str | None = None,
        index_prefix: str = CACHE_KEY,
    ):
        self.redis = redis_client
        self.threshold = threshold
        self.provider = provider or EmbeddingProvider()
        self.index_name = index_name or f"{PREFIX}:semantic_cache_idx_v{EMBEDDING_DIM}"
        self.index_prefix = index_prefix
        self.vector_field = "embedding_vector"
        self.knn_available = False
        self.last_lookup_backend = "unavailable"
        self._ensure_index()

    def _ensure_index(self) -> None:
        if not hasattr(self.redis, "ft") or self.redis.__class__.__name__ == "MemoryRedis":
            self.last_lookup_backend = "offline_test_backend"
            return
        try:
            from redis.commands.search.field import TagField, TextField, VectorField
            from redis.commands.search.index_definition import IndexDefinition, IndexType

            fields = [TextField("$.query"), TagField("$.signature"), TextField("$.data_version"),
                      VectorField("$.embedding", "HNSW", {"TYPE": "FLOAT32", "DIM": EMBEDDING_DIM,
                                                           "DISTANCE_METRIC": "COSINE"},
                                  as_name=self.vector_field)]
            index = self.redis.ft(self.index_name)
            try:
                info = index.info()
                vector_attrs = []
                for attribute in info.get("attributes", []):
                    values = dict(zip(attribute[::2], attribute[1::2]))
                    if values.get(b"type") == b"VECTOR":
                        vector_attrs.append(values)
                vector_info = vector_attrs[0] if vector_attrs else {}
                identifier = vector_info.get(b"identifier", b"").decode()
                dimension = int(vector_info.get(b"dim", 0))
                if identifier != self.vector_field or dimension != EMBEDDING_DIM:
                    index.dropindex(delete_documents=False)
                    index.create_index(fields, definition=IndexDefinition(
                        prefix=[f"{self.index_prefix}:"], index_type=IndexType.JSON))
            except Exception as info_exc:
                message = str(info_exc).lower()
                if "unknown index name" not in message and "no such index" not in message:
                    raise
                index.create_index(fields, definition=IndexDefinition(
                    prefix=[f"{self.index_prefix}:"], index_type=IndexType.JSON))
            self.knn_available = True
            self.last_lookup_backend = "redis_knn"
        except Exception as exc:
            self.knn_available = False
            log.error("Redis KNN index unavailable: %s", exc)

    def _current_version(self, restaurant_id: int | None = None) -> str:
        key = f"{DATA_VERSION_KEY}:{restaurant_id or 'global'}"
        value = self.redis.get(key)
        return str(value or "0")

    def _get_record(self, key: str) -> dict[str, Any] | None:
        if hasattr(self.redis, "json"):
            record = self.redis.json().get(key)
            if record is not None:
                return record
        raw = self.redis.get(key)
        if not raw:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode()
        return json.loads(raw)

    def invalidate_restaurant(self, restaurant_id: int) -> str:
        key = f"{DATA_VERSION_KEY}:{restaurant_id}"
        return str(self.redis.incr(key))

    def put(self, query: str, answer: str, signature: str, restaurant_id: int | None = None) -> str:
        cache_id = uuid.uuid4().hex
        record = {
            "query": query,
            "answer": answer,
            "signature": signature,
            "embedding": self.provider.embed(query),
            "data_version": self._current_version(restaurant_id),
            "restaurant_id": restaurant_id,
            "created_at": time.time(),
        }
        key = f"{CACHE_KEY}:{cache_id}"
        if hasattr(self.redis, "json"):
            self.redis.json().set(key, "$", record)
        else:
            self.redis.set(key, json.dumps(record))
        self.redis.sadd(f"{CACHE_KEY}:ids", cache_id)
        return cache_id

    def _offline_lookup(
        self, signature: str, embedding: list[float], restaurant_id: int | None, current_version: str
    ) -> tuple[dict[str, Any] | None, float]:
        """Explicit in-memory fallback for unit tests without Redis Search."""
        best: tuple[dict[str, Any] | None, float] = (None, 0.0)
        for raw_id in self.redis.smembers(f"{CACHE_KEY}:ids"):
            cache_id = raw_id.decode() if isinstance(raw_id, bytes) else str(raw_id)
            record = self._get_record(f"{CACHE_KEY}:{cache_id}")
            if not record:
                continue
            if (record.get("data_version") != current_version
                    or record.get("signature") != signature
                    or record.get("restaurant_id") != restaurant_id):
                continue
            score = cosine_similarity(embedding, record.get("embedding", []))
            if score > best[1]:
                best = (record | {"cache_id": cache_id}, score)
        return best if best[1] >= self.threshold else (None, best[1])

    def _redis_knn_lookup(
        self, signature: str, embedding: list[float], restaurant_id: int | None, current_version: str
    ) -> tuple[dict[str, Any] | None, float]:
        from redis.commands.search.query import Query

        query = Query(f"*=>[KNN 1000 @{self.vector_field} $query_vector AS vector_distance]")
        query = query.sort_by("vector_distance").return_fields("vector_distance").paging(0, 1000).dialect(2)
        packed = struct.pack(f"{len(embedding)}f", *embedding)
        try:
            result = self.redis.ft(self.index_name).search(query, query_params={"query_vector": packed})
        except Exception as exc:
            log.error("Redis KNN query failed: %s", exc)
            raise RuntimeError("Redis KNN query failed") from exc
        best: tuple[dict[str, Any] | None, float] = (None, 0.0)
        for document in result.docs:
            record = self._get_record(document.id)
            if not record:
                continue
            if (record.get("data_version") != current_version
                    or record.get("signature") != signature
                    or record.get("restaurant_id") != restaurant_id):
                continue
            raw_distance = getattr(document, "vector_distance", None)
            if raw_distance is None:
                continue
            try:
                similarity = max(0.0, min(1.0, 1.0 - float(raw_distance)))
            except (TypeError, ValueError):
                continue
            if similarity > best[1]:
                best = (record | {"cache_id": document.id}, similarity)
        return best if best[1] >= self.threshold else (None, best[1])

    def lookup(self, query: str, signature: str, restaurant_id: int | None = None) -> tuple[dict[str, Any] | None, float]:
        embedding = self.provider.embed(query)
        current_version = self._current_version(restaurant_id)
        if self.knn_available:
            self.last_lookup_backend = "redis_knn"
            return self._redis_knn_lookup(signature, embedding, restaurant_id, current_version)
        if not hasattr(self.redis, "ft") or self.redis.__class__.__name__ == "MemoryRedis":
            self.last_lookup_backend = "offline_test_backend"
            return self._offline_lookup(signature, embedding, restaurant_id, current_version)
        raise RuntimeError("Redis KNN is unavailable; live lookup was not downgraded to a record scan")

    def answer(self, query: str, signature: str, agent: Callable[[], str], restaurant_id: int | None = None) -> CacheResult:
        started = time.perf_counter()
        lookup_start = time.perf_counter()
        record, similarity = self.lookup(query, signature, restaurant_id)
        lookup_ms = (time.perf_counter() - lookup_start) * 1000
        if record:
            total_ms = (time.perf_counter() - started) * 1000
            log.info("Semantic cache hit similarity=%.4f query=%s", similarity, query)
            return CacheResult(record["answer"], True, similarity, lookup_ms, 0.0, total_ms, False, record["cache_id"])
        log.info("Semantic cache miss query=%s", query)
        agent_start = time.perf_counter()
        answer = agent()
        agent_ms = (time.perf_counter() - agent_start) * 1000
        cache_id = self.put(query, answer, signature, restaurant_id)
        total_ms = (time.perf_counter() - started) * 1000
        return CacheResult(answer, False, similarity, lookup_ms, agent_ms, total_ms, True, cache_id)
