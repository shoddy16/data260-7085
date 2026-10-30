import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from hw8_config import DOMAIN_ID, PREFIX, SEED, SID4, VERIFY_SEED
from kafka_protocol import EntityWorker
from pipeline import KafkaPipeline


def main() -> int:
    worker = EntityWorker()
    cid = "hw8-smoke-correlation"
    data = {
        "restaurantName": "Smoke Restaurant",
        "location": "San Jose",
        "email": "smoke@example.com",
        "description": "inspection",
        "category": "restaurant",
        "score": 90,
    }
    created = worker.process(
        {"correlation_id": cid, "reply_to": f"{PREFIX}_entity_responses", "operation": "CREATE_ENTITY", "data": data}
    )
    fetched = worker.process(
        {
            "correlation_id": "get",
            "reply_to": f"{PREFIX}_entity_responses",
            "operation": "GET_ENTITY",
            "data": {"entity_id": created["entity_id"]},
        }
    )
    final = KafkaPipeline().run_once("restaurant inspection smoke", "smoke-pipeline")
    checks = [
        {"name": "CREATE_ENTITY returns UUID", "passed": bool(created.get("entity_id"))},
        {
            "name": "GET_ENTITY round trip",
            "passed": fetched.get("entity", {}).get("entity_id") == created.get("entity_id"),
        },
        {"name": "correlation preserved", "passed": created.get("correlation_id") == cid},
        {"name": "pipeline final JSON", "passed": final.get("status") == "approved"},
    ]
    record = {
        "homework": 8,
        "SID4": SID4,
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "model": "llama3.2:3b",
        "configuration": {"PREFIX": PREFIX, "DOMAIN_ID": DOMAIN_ID, "SEED": SEED, "VERIFY_SEED": VERIFY_SEED},
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }
    out = Path("reports/hw08/verification.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return 0 if all(item["passed"] for item in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
