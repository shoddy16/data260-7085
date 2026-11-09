"""Run the qualifying five-threshold sweep with live Ollama and Redis KNN."""

from __future__ import annotations

import json
import time
from pathlib import Path

import redis
import yaml

from hw9_cache import EmbeddingProvider, SemanticCache
from routers.hw9 import query_signature

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "reports" / "hw09" / "raw" / "threshold_sweep_qualifying_knn.json"
THRESHOLDS = (0.75, 0.80, 0.85, 0.90, 0.95)


def main() -> None:
    client = redis.Redis(host="localhost", port=6380, decode_responses=True)
    provider = EmbeddingProvider()
    probe = provider.embed("HW9 live embedding probe")
    if provider._ollama_unavailable:
        raise RuntimeError("Ollama embeddings were unavailable; qualifying sweep was not run")
    if len(probe) != 768:
        raise RuntimeError(f"Expected 768-dimensional embeddings, got {len(probe)}")
    cases = yaml.safe_load((ROOT / "cache_cases.yaml").read_text(encoding="utf-8"))["cases"]
    reference_queries = [case["query"] for case in cases[:10]]
    answers = {query: f"verified answer for {query}" for query in reference_queries}
    all_results: list[dict] = []
    cleanup: list[tuple[str, str, str]] = []
    try:
        for threshold in THRESHOLDS:
            restaurant_id = 991000 + int(threshold * 100)
            cache = SemanticCache(client, threshold=threshold, provider=provider)
            ids: list[str] = []
            for query in reference_queries:
                cache_id = cache.put(query, answers[query], query_signature(query), restaurant_id)
                ids.append(cache_id)
            cleanup.extend((cache_id, str(restaurant_id), f"{cache.index_name}") for cache_id in ids)
            hits = false_hits = correct_hits = missed_expected_hits = 0
            latencies: list[float] = []
            false_hit_examples: list[dict] = []
            backend_values: set[str] = set()
            for case in cases:
                index = int(case["id"].split("-")[-1]) - 1
                seed_query = reference_queries[index % len(reference_queries)]
                query = seed_query if case["category"] == "exact_duplicate" else case["query"]
                started = time.perf_counter()
                record, similarity = cache.lookup(query, query_signature(query), restaurant_id)
                latencies.append((time.perf_counter() - started) * 1000)
                backend_values.add(cache.last_lookup_backend)
                is_hit = record is not None
                if is_hit:
                    hits += 1
                    if case["expected"] == "hit":
                        correct_hits += 1
                    else:
                        false_hits += 1
                        if not false_hit_examples:
                            false_hit_examples.append({
                                "cached_query": record["query"],
                                "incoming_query": query,
                                "similarity": similarity,
                                "threshold": threshold,
                                "cached_answer": record["answer"],
                                "correct_answer": "miss by frozen label",
                            })
                elif case["expected"] == "hit":
                    missed_expected_hits += 1
            misses = len(cases) - hits
            all_results.append({
                "threshold": threshold,
                "cases": len(cases),
                "expected_hits": 20,
                "expected_misses": 20,
                "cache_hits": hits,
                "cache_misses": misses,
                "correct_hits": correct_hits,
                "false_hits": false_hits,
                "missed_expected_hits": missed_expected_hits,
                "hit_rate": hits / 40,
                "false_hit_rate": false_hits / 20,
                "false_hit_rate_all_cases": false_hits / 40,
                "mean_latency_ms": sum(latencies) / len(latencies),
                "total_cost": misses * 1.0 + false_hits * 8.0,
                "cost_model": {"cache_miss": 1.0, "false_hit": 8.0},
                "embedding_model": provider.model,
                "embedding_dim": len(probe),
                "live_embeddings": True,
                "redis_knn": backend_values == {"redis_knn"},
                "backend_values": sorted(backend_values),
                "false_hit_examples": false_hit_examples,
            })
    finally:
        for cache_id, _restaurant_id, _index_name in cleanup:
            client.delete(f"s7085:semantic_cache:{cache_id}")
            client.srem("s7085:semantic_cache:ids", cache_id)
    payload = {
        "status": "PASS" if all(row["redis_knn"] for row in all_results) else "FAIL",
        "dataset": "cache_cases.yaml",
        "qualifying": True,
        "method": "live Ollama nomic-embed-text embeddings and Redis HNSW KNN",
        "thresholds": all_results,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
