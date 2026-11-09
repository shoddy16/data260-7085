"""Reproducible offline HW9 cache and self-improvement measurements."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import yaml

from hw9_agents import run_variants
from hw9_cache import EmbeddingProvider, SemanticCache
from routers.hw9 import MemoryRedis, query_signature

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "reports" / "hw09" / "raw"


def offline_embedding(text: str) -> list[float]:
    digest = hashlib.sha256(text.lower().encode()).digest()
    return [float(value) / 255.0 for value in digest[:16]]


def threshold_sweep() -> list[dict]:
    cases = yaml.safe_load((ROOT / "cache_cases.yaml").read_text(encoding="utf-8"))["cases"]
    answers = {case["query"]: f"verified answer for {case['query']}" for case in cases}
    reference_queries = [case["query"] for case in cases[:10]]
    results = []
    live = os.getenv("HW9_LIVE_EMBEDDINGS") == "1"
    provider = EmbeddingProvider() if live else EmbeddingProvider(offline_embedding)
    for threshold in (0.75, 0.80, 0.85, 0.90, 0.95):
        redis = MemoryRedis()
        cache = SemanticCache(redis, threshold=threshold, provider=provider)
        for query in reference_queries:
            cache.put(query, answers[query], query_signature(query))
        hits = false_hits = 0
        latencies = []
        for case in cases:
            index = int(case["id"].split("-")[-1]) - 1
            seed_query = reference_queries[index % len(reference_queries)]
            query = seed_query if case["category"] == "exact_duplicate" else case["query"]
            started = time.perf_counter()
            result = cache.answer(query, query_signature(query), lambda q=query: answers.get(q, "verified answer"))
            latencies.append((time.perf_counter() - started) * 1000)
            if result.is_cached:
                hits += 1
                if case["expected"] == "miss":
                    false_hits += 1
        miss_cost, false_hit_cost = 1.0, 8.0
        misses = len(cases) - hits
        results.append({
            "threshold": threshold,
            "cases": len(cases),
            "cache_hits": hits,
            "false_hits": false_hits,
            "hit_rate": hits / len(cases),
            "false_hit_rate": false_hits / len(cases),
            "mean_latency_ms": sum(latencies) / len(latencies),
            "total_cost": misses * miss_cost + false_hits * false_hit_cost,
            "cost_model": {"cache_miss": miss_cost, "false_hit": false_hit_cost},
            "embedding_model": provider.model if live else "offline_sha256",
            "embedding_dim": len(provider.embed(reference_queries[0])),
            "live_embeddings": live,
        })
    return results


def false_hit_example() -> dict:
    cases = yaml.safe_load((ROOT / "cache_cases.yaml").read_text(encoding="utf-8"))["cases"]
    references = [case["query"] for case in cases[:10]]
    cache = SemanticCache(MemoryRedis(), threshold=0.75, provider=EmbeddingProvider(offline_embedding))
    for query in references:
        cache.put(query, f"answer for {query}", query_signature(query))
    for case in cases:
        if case["expected"] != "miss":
            continue
        record, score = cache.lookup(case["query"], query_signature(case["query"]))
        if record:
            return {"cached_query": record["query"], "incoming_query": case["query"], "similarity": score,
                    "threshold": 0.75, "cached_answer": record["answer"], "correct_answer": "miss by frozen label"}
    return {"status": "not_found"}


def stale_invalidation_example() -> dict:
    cache = SemanticCache(MemoryRedis(), provider=EmbeddingProvider(lambda _: [1.0, 0.0]))
    first = cache.answer("Sunrise score", "score_below", lambda: "65", restaurant_id=7)
    cache.invalidate_restaurant(7)
    second = cache.answer("Sunrise score", "score_below", lambda: "60", restaurant_id=7)
    return {"initial": first.__dict__, "after_version_increment": second.__dict__, "old_answer_reused": second.answer == "65"}


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    sweep = threshold_sweep()
    (RAW / "threshold_sweep.json").write_text(json.dumps(sweep, indent=2), encoding="utf-8")
    (RAW / "false_hit_example.json").write_text(json.dumps(false_hit_example(), indent=2), encoding="utf-8")
    (RAW / "stale_invalidation.json").write_text(json.dumps(stale_invalidation_example(), indent=2), encoding="utf-8")
    reference = ROOT / "data" / "hw9" / "reference_data.json"
    lessons = ROOT / "data" / "hw9" / "lessons_experiment.json"
    questions = list(json.loads(reference.read_text(encoding="utf-8")))
    variants = run_variants(questions, reference, lessons)
    (RAW / "self_improvement_variants.json").write_text(json.dumps(variants, indent=2), encoding="utf-8")
    print(json.dumps({"thresholds": sweep, "variants": variants}, indent=2))


if __name__ == "__main__":
    main()
