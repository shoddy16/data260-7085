from __future__ import annotations

"""Run repeatable HW5 checks and record truthful verified evidence."""

import ast
import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "reports" / "hw05"
RAW = REPORT / "raw"
checks: list[dict] = []


def record(name: str, passed: bool, details: dict | None = None) -> None:
    checks.append({"name": name, "passed": bool(passed), **(details or {})})


def run_check(name: str, command: list[str], *, cwd: Path = ROOT, isolated: bool = False) -> None:
    env = dict(os.environ)
    if isolated:
        env["DATABASE_URL"] = "sqlite://"
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=180)
    record(name, result.returncode == 0, {
        "exit_code": result.returncode,
        "output_tail": (result.stdout + result.stderr)[-1200:],
    })


# Tests run with an isolated in-memory SQLite database.
run_check("Python unittest suite", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"], isolated=True)
run_check("Offline assertion runner", [sys.executable, "run_offline_tests.py"], isolated=True)
run_check("Frontend production build", [r"C:\Program Files\nodejs\npm.cmd", "run", "build"], cwd=ROOT / "frontend")


def declared_tools(path: str) -> list[str]:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    return [node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and any(isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)
                    and dec.func.attr == "tool" for dec in node.decorator_list)]


meal_names = declared_tools("meals_server.py")
domain_names = declared_tools("domain_mcp_server.py")
record("Meals server declares four required tools", set(meal_names) == {
    "search_meals_by_name", "meals_by_ingredient", "random_meal", "meal_details"
}, {"tools": meal_names})
record("Domain server declares exactly three tools", set(domain_names) == {
    "search", "detail_lookup", "aggregate"
}, {"tools": domain_names})

# Live MySQL inspection and GET-only API checks; no writes are issued here.
try:
    os.environ.pop("DATABASE_URL", None)
    from sqlalchemy import inspect, text
    from database.database import engine
    from fastapi.testclient import TestClient
    from main import app

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("inspections")}
    required = {"restaurant_id", "inspection_code", "score", "created_at", "updated_at"}
    with engine.connect() as connection:
        restaurant_count = connection.execute(text("SELECT COUNT(*) FROM restaurants")).scalar_one()
        inspection_count = connection.execute(text("SELECT COUNT(*) FROM inspections")).scalar_one()
        invalid_links = connection.execute(text("SELECT COUNT(*) FROM inspections WHERE restaurant_id IS NULL OR inspection_code IS NULL OR score IS NULL")).scalar_one()
        duplicate_codes = connection.execute(text("SELECT COUNT(*) FROM (SELECT inspection_code FROM inspections GROUP BY inspection_code HAVING COUNT(*) > 1) d")).scalar_one()
    foreign_keys = inspector.get_foreign_keys("inspections")
    restrictive_fk = any(
        "restaurant_id" in fk.get("constrained_columns", [])
        and fk.get("options", {}).get("ondelete", "").upper() == "RESTRICT"
        for fk in foreign_keys
    )
    record("Configured MySQL contains migrated HW5 schema/data", required <= columns and restaurant_count >= 1 and inspection_count == 5000 and invalid_links == 0 and duplicate_codes == 0 and restrictive_fk, {
        "restaurant_count": restaurant_count,
        "inspection_count": inspection_count,
        "inspection_columns_present": sorted(required & columns),
        "unlinked_or_incomplete_inspections": invalid_links,
        "duplicate_inspection_codes": duplicate_codes,
        "restrictive_restaurant_fk": restrictive_fk,
    })
    with TestClient(app) as client:
        api_statuses = {
            "/restaurants/?skip=0&limit=1": client.get("/restaurants/?skip=0&limit=1").status_code,
            "/inspections/?skip=0&limit=1": client.get("/inspections/?skip=0&limit=1").status_code,
        }
    record("Live MySQL paginated API GET endpoints", all(status == 200 for status in api_statuses.values()), {"http_statuses": api_statuses})
except Exception as exc:
    record("Configured MySQL schema and paginated API", False, {"error_type": type(exc).__name__, "error": str(exc)[:300]})

# Validate saved outputs from actual live runs; never generate substitute outputs here.
def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

try:
    meals = load_json(RAW / "mealdb_live_results.json")
    names = {item["tool"] for item in meals["results"] if item.get("ok")}
    expected = {"search_meals_by_name", "meals_by_ingredient", "random_meal", "meal_details"}
    record("Saved live TheMealDB calls cover four tools", names == expected, {"successful_tools": sorted(names), "verified_at_utc": meals.get("verified_at_utc")})
except Exception as exc:
    record("Saved live TheMealDB outputs", False, {"error_type": type(exc).__name__})

try:
    mcp = load_json(RAW / "mcp_stdio_results.json")
    discovered = {item["server_script"]: set(item["discovered_tools"]) for item in mcp["results"]}
    ok = discovered.get("meals_server.py") == expected and discovered.get("domain_mcp_server.py") == {"search", "detail_lookup", "aggregate"}
    record("Saved live MCP stdio discovery for both servers", ok, {"discovered_tools": {name: sorted(value) for name, value in discovered.items()}, "verified_at_utc": mcp.get("verified_at_utc")})
except Exception as exc:
    record("Saved live MCP stdio discovery", False, {"error_type": type(exc).__name__})

try:
    scenarios = load_json(RAW / "agent_scenario_summary.json")
    good = len(scenarios) == 4 and all(item.get("stop_reason") == "normal_completion" and item.get("tool_call_count", 0) > 0 for item in scenarios)
    record("Four saved real Ollama scenarios completed normally", good, {"scenario_count": len(scenarios), "run_ids": [item.get("run_id") for item in scenarios]})
except Exception as exc:
    record("Four saved real Ollama scenarios", False, {"error_type": type(exc).__name__})

try:
    with (RAW / "fault_injection_records.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    rates = {}
    for row in rows:
        key = row.get("failure_rate", row.get("configured_failure_rate", row.get("failure_probability", "unknown")))
        rates[key] = rates.get(key, 0) + 1
    record("Saved fault-injection raw data has 150 calls", len(rows) == 150, {"record_count": len(rows), "rate_column_counts": rates})
except Exception as exc:
    record("Saved fault-injection raw records", False, {"error_type": type(exc).__name__})

commit_result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
commit = commit_result.stdout.strip() if commit_result.returncode == 0 else None
screenshots_dir = REPORT / "screenshots"
screenshot_count = len(list(screenshots_dir.glob("*.png"))) if screenshots_dir.exists() else 0
all_checks = all(item["passed"] for item in checks)
payload = {
    "homework": 5,
    "SID4": 7085,
    "base_commit_head": commit,
    "working_tree_changes_included": True,
    "branch": "hw5",
    "model_configuration": {"provider": "Ollama", "model": "llama3.2:3b", "url": "http://localhost:11434"},
    "SEED": 7085,
    "VERIFY_SEED": 267085,
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "checks": checks,
    "checks_passed": all_checks,
    "screenshots_saved": screenshot_count,
    "final_verification": False,
    "submission_ready": False,
    "remaining": ["Required GUI screenshots", "final PDF export", "final Git review/commit/tag"],
    "note": "This artifact records actual checks and evidence available before manual screenshots and final Git tagging. It is not final submission verification.",
}
REPORT.mkdir(parents=True, exist_ok=True)
(REPORT / "verification.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2, ensure_ascii=False))
raise SystemExit(0 if all_checks else 1)
