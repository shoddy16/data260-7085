"""Validate Redis HNSW KNN behavior against the live HW9 Redis instance."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import redis

from hw9_cache import EmbeddingProvider, SemanticCache
from hw9_config import CACHE_KEY, DATA_VERSION_KEY

OUT = Path("reports/hw09/raw/live_knn_validation.json")
TEST_RESTAURANT = 990001


def main() -> None:
    client = redis.Redis(host="localhost", port=6380, decode_responses=True)
    cache = SemanticCache(client, threshold=0.85, provider=EmbeddingProvider())
    index_info = client.ft(cache.index_name).info()
    vector_attrs = [
        dict(zip(attribute[::2], attribute[1::2]))
        for attribute in index_info["attributes"]
        if dict(zip(attribute[::2], attribute[1::2])).get("type") == "VECTOR"
    ]
    cases = [
        ("exact", "Which restaurants scored below 70?", "knn_exact"),
        ("paraphrase", "List restaurants with scores under 70", "knn_exact"),
        ("logical_difference", "Which restaurants scored above 70?", "knn_no_match"),
        ("unrelated", "Explain binary search", "knn_no_match"),
    ]
    temporary_ids: list[str] = []
    results: dict[str, object] = {
        "backend": cache.last_lookup_backend,
        "index_name": cache.index_name,
        "vector_attribute": vector_attrs[0] if vector_attrs else {},
        "embedding_dimension": len(cache.provider.embed(cases[0][1])),
        "cases": [],
    }
    try:
        cache_id = cache.put(cases[0][1], "temporary KNN answer", "knn_exact", TEST_RESTAURANT)
        temporary_ids.append(cache_id)
        for label, query, signature in cases:
            record, similarity = cache.lookup(query, signature, TEST_RESTAURANT)
            results["cases"].append({
                "label": label,
                "query": query,
                "signature": signature,
                "is_cached": record is not None,
                "similarity": similarity,
                "backend": cache.last_lookup_backend,
                "matched_query": record.get("query") if record else None,
            })

        before, before_score = cache.lookup(cases[0][1], "knn_exact", TEST_RESTAURANT)
        new_version = cache.invalidate_restaurant(TEST_RESTAURANT)
        after, after_score = cache.lookup(cases[0][1], "knn_exact", TEST_RESTAURANT)
        results["stale_guard"] = {
            "before_cached": before is not None,
            "before_similarity": before_score,
            "new_version": new_version,
            "after_cached": after is not None,
            "after_similarity": after_score,
        }

        concurrent_id = cache.put(cases[0][1], "temporary concurrent answer", "knn_exact", TEST_RESTAURANT)
        temporary_ids.append(concurrent_id)
        with ThreadPoolExecutor(max_workers=4) as executor:
            concurrent = list(executor.map(
                lambda _: cache.lookup(cases[0][1], "knn_exact", TEST_RESTAURANT)[1], range(8)
            ))
        results["concurrent"] = {
            "workers": 4,
            "queries": len(concurrent),
            "all_backend_knn": cache.last_lookup_backend == "redis_knn",
            "all_cached": all(score >= cache.threshold for score in concurrent),
            "similarities": concurrent,
        }

        empty = redis.Redis(host="localhost", port=6380, decode_responses=True)
        empty_cache = SemanticCache(
            empty,
            threshold=0.85,
            provider=EmbeddingProvider(),
            index_name="s7085:semantic_cache_empty_idx_v768",
            index_prefix="s7085:semantic_cache_empty",
        )
        empty_record, empty_score = empty_cache.lookup("empty index query", "empty_signature")
        results["empty_index"] = {
            "is_cached": empty_record is not None,
            "similarity": empty_score,
            "backend": empty_cache.last_lookup_backend,
        }
        empty.ft(empty_cache.index_name).dropindex(delete_documents=False)
    finally:
        for cache_id in temporary_ids:
            client.delete(f"{CACHE_KEY}:{cache_id}")
            client.srem(f"{CACHE_KEY}:ids", cache_id)
        client.delete(f"{DATA_VERSION_KEY}:{TEST_RESTAURANT}")
    results["status"] = "PASS" if results["backend"] == "redis_knn" else "FAIL"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
