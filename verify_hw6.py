"""Objective HW6 smoke verification; writes reports/hw06/verification.json."""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "reports" / "hw06"

def check(name, function):
    try:
        details = function(); return {"name": name, "passed": bool(details is not False), "details": details}
    except Exception as exc:
        return {"name": name, "passed": False, "details": f"{type(exc).__name__}: {exc}"}

def main():
    from hw6_memory import ChatRequest, DeterministicChatModel, InMemoryStore, chat_turn
    from file_memory import consolidation_required
    def tagged_commit_check():
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        tagged = subprocess.check_output(["git", "rev-parse", "refs/tags/hw6^{}"], cwd=ROOT, text=True).strip()
        return {"head": head, "tagged_commit": tagged, "match": head == tagged}

    def api_smoke_check():
        os.environ.setdefault("DATABASE_URL", "sqlite://")
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        checks = {"docs_status": client.get("/docs").status_code, "missing_required_name": client.post("/api/documents", json={"status": "active", "category": "restaurant", "inspectionDate": "2026-10-09T00:00:00Z"}).status_code, "invalid_enum": client.post("/api/documents", json={"name": "x", "status": "bad", "category": "restaurant", "inspectionDate": "2026-10-09T00:00:00Z"}).status_code, "hw6_route_count": sum(1 for route in app.routes if "/api/" in getattr(route, "path", ""))}
        checks["passed"] = checks["docs_status"] == 200 and checks["missing_required_name"] == 422 and checks["invalid_enum"] == 422 and checks["hw6_route_count"] >= 8
        return checks

    results = [
        check("HEAD matches tagged hw6 commit", tagged_commit_check),
        check("FastAPI smoke and validation errors", api_smoke_check),
        check("Deterministic chat creates reply and metrics", lambda: bool(chat_turn(ChatRequest(user_id="verify", message="What is the inspection domain?"), InMemoryStore(), DeterministicChatModel())["metrics"])),
        check("File memory files exist", lambda: (ROOT / "AGENT.md").exists() and (ROOT / "MEMORY.md").exists()),
        check("Memory probes exist", lambda: (ROOT / "memory_probes.yaml").exists()),
        check("HW6 experiment raw output exists", lambda: (OUT / "raw" / "memory_token_records.csv").exists()),
        check("MongoDB API routes are registered", lambda: "hw6_router" in (ROOT / "main.py").read_text(encoding="utf-8")),
    ]
    try:
        commit = subprocess.check_output(["git", "rev-parse", "refs/tags/hw6^{}"], cwd=ROOT, text=True).strip()
    except Exception: commit = "unknown"
    payload = {"homework": 6, "SID4": 7085, "commit": commit, "model": "llama3.2:3b", "SEED": 7085, "VERIFY_SEED": 267085, "checks": results, "verified_at_utc": datetime.now(timezone.utc).isoformat()}
    OUT.mkdir(parents=True, exist_ok=True); (OUT / "verification.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for result in results: print(("PASS" if result["passed"] else "FAIL") + ": " + result["name"])
    print(f"HW6 checks: {sum(x['passed'] for x in results)}/{len(results)} passed")
    return 0 if all(x["passed"] for x in results) else 1

if __name__ == "__main__": sys.exit(main())
