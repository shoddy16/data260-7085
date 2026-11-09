"""Run the HW9 API smoke test with SQLite and the in-process Redis fallback."""

import json
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi.testclient import TestClient

from main import app


def main():
    client = TestClient(app)
    health = client.get("/hw9/health")
    first = client.post("/hw9/ask", json={"question": "Which restaurants scored below 70?"})
    second = client.post("/hw9/ask", json={"question": "Which restaurants scored below 70?"})
    payload = {
        "health": {"status_code": health.status_code, "body": health.json()},
        "first_request": {"status_code": first.status_code, "body": first.json()},
        "duplicate_request": {"status_code": second.status_code, "body": second.json()},
        "status": "PASS" if health.status_code == first.status_code == second.status_code == 200 and second.json()["is_cached"] else "FAIL",
        "live_services": False,
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
