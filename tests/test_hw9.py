import json
import tempfile
from pathlib import Path

import pytest

import hw9_cache
from hw9_agents import SelfImprovingSystem
from hw9_cache import EmbeddingProvider, SemanticCache, ViewCounter
from routers.hw9 import MemoryRedis


class FakeRestaurant:
    id = object()

    def __init__(self, restaurant_id=7):
        self.id = restaurant_id
        self.views = 0


class FakeQuery:
    def __init__(self, restaurant):
        self.restaurant = restaurant

    def filter(self, _condition):
        return self

    def first(self):
        return self.restaurant


class FakeDB:
    def __init__(self, restaurant=None):
        self.restaurant = restaurant
        self.commits = 0
        self.rollbacks = 0

    def query(self, _model):
        return FakeQuery(self.restaurant)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def test_view_counter_syncs_each_tenth_and_keeps_ids_independent(monkeypatch):
    monkeypatch.setattr(hw9_cache, "RestaurantModel", FakeRestaurant)
    redis = MemoryRedis()
    restaurant = FakeRestaurant(7)
    db = FakeDB(restaurant)
    counter = ViewCounter(redis)
    assert [counter.increment_restaurant_views(7, db) for _ in range(2)] == [1, 2]
    assert [counter.increment_restaurant_views(7, db) for _ in range(8)][-1] == 10
    assert restaurant.views == 10
    assert db.commits == 1
    assert counter.increment_restaurant_views(7, db) == 11
    assert counter.increment_restaurant_views(8, db) == 1
    assert counter.increment_restaurant_views(7, db) == 12


def test_view_counter_translates_redis_failure(monkeypatch):
    class BrokenRedis:
        def incr(self, _key):
            raise OSError("redis unavailable")

    monkeypatch.setattr(hw9_cache, "RestaurantModel", FakeRestaurant)
    with pytest.raises(RuntimeError, match="Unable to increment"):
        ViewCounter(BrokenRedis()).increment_restaurant_views(1, FakeDB(FakeRestaurant(1)))


def test_semantic_cache_hit_version_and_signature_guards():
    def embed(text):
        return [1.0, 0.0] if "sunrise" in text.lower() else [0.0, 1.0]

    cache = SemanticCache(MemoryRedis(), threshold=0.85, provider=EmbeddingProvider(embed))
    calls = []
    miss = cache.answer("Sunrise score", "score_below", lambda: calls.append(1) or "65", 7)
    hit = cache.answer("Sunrise score", "score_below", lambda: calls.append(1) or "wrong", 7)
    assert miss.is_cached is False
    assert hit.is_cached is True
    assert hit.agent_executed is False
    assert len(calls) == 1
    assert cache.answer("Sunrise score", "score_above", lambda: "95", 7).is_cached is False
    cache.invalidate_restaurant(7)
    assert cache.answer("Sunrise score", "score_below", lambda: "updated", 7).is_cached is False


def test_self_improving_system_is_bounded_and_persists_lesson():
    with tempfile.TemporaryDirectory(dir=Path.cwd() / "reports") as directory:
        tmp_path = Path(directory)
        reference = tmp_path / "reference.json"
        lessons = tmp_path / "lessons.json"
        reference.write_text(json.dumps({"Q": "verified fact"}), encoding="utf-8")
        lessons.write_text("[]", encoding="utf-8")
        system = SelfImprovingSystem(reference, lessons)
        system.answerer.forced_first_answers = {"Q": "wrong"}
        result = system.run("Q")
        assert result["attempts"] == 2
        assert result["final_evaluation"] == "PASS"
        saved = json.loads(lessons.read_text(encoding="utf-8"))
        assert saved[0]["lesson_id"] and "correction" in saved[0]
