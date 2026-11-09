"""Objective offline smoke verification for the HW9 implementation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from hw9_agents import SelfImprovingSystem
from hw9_cache import EmbeddingProvider, SemanticCache, ViewCounter
from routers.hw9 import MemoryRedis

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "reports" / "hw09" / "verification.json"


def check(name, function):
    try:
        function()
        return {"name": name, "status": "PASS"}
    except Exception as exc:  # pragma: no cover - verification boundary
        return {"name": name, "status": "FAIL", "error": repr(exc)}


def main():
    reference = ROOT / "data" / "hw9" / "reference_data.json"
    checks = [
        check("redis_view_counter_api", lambda: ViewCounter(MemoryRedis()).redis.incr("s7085:views:restaurant:1") == 1),
        check("cache_exact_hit", lambda: _cache_hit()),
        check("self_improvement_bounded", lambda: _bounded(reference)),
        check("cache_cases_has_40_cases", lambda: _case_count()),
    ]
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        commit = "working-tree"
    payload = {
        "homework": "HW9",
        "sid4": 7085,
        "commit": commit,
        "configuration": {"PORT_BASE": 8085, "HW9_PORT": 8086, "PREFIX": "s7085", "SEED": 7085, "VERIFY_SEED": 267085, "DOMAIN_ID": 5},
        "model": "llama3.2:3b",
        "checks": checks,
        "status": "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


def _cache_hit():
    cache = SemanticCache(MemoryRedis(), provider=EmbeddingProvider(lambda _: [1.0, 0.0]))
    first = cache.answer("q", "general", lambda: "answer")
    second = cache.answer("q", "general", lambda: "wrong")
    assert not first.is_cached and second.is_cached and not second.agent_executed


def _bounded(reference):
    system = SelfImprovingSystem(reference, ROOT / "data" / "hw9" / "lessons.json")
    result = system.run("Which restaurants scored below 70?", save_lesson=False)
    assert 1 <= result["attempts"] <= 2


def _case_count():
    import yaml
    cases = yaml.safe_load((ROOT / "cache_cases.yaml").read_text(encoding="utf-8"))["cases"]
    assert len(cases) == 40


if __name__ == "__main__":
    main()
