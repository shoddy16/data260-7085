"""Run live semantic-cache correctness cases against the Docker API."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx


CASES = [
    ("exact_seed", "Which restaurants scored below 70?"),
    ("exact_duplicate", "Which restaurants scored below 70?"),
    ("paraphrase", "List restaurants with scores under 70"),
    ("similar_different_answer", "Which restaurants scored above 70?"),
    ("unrelated", "Explain binary search"),
]


def main() -> None:
    rows = []
    with httpx.Client(base_url="http://127.0.0.1:8086", timeout=180) as client:
        for category, question in CASES:
            response = client.post("/hw9/ask", json={"question": question})
            rows.append({"category": category, "question": question, "status_code": response.status_code, "body": response.json()})
    payload = {"timestamp": datetime.now(timezone.utc).isoformat(), "embedding_model": "nomic-embed-text", "dimension": 768, "cases": rows}
    output = Path(__file__).resolve().parent / "reports" / "hw09" / "raw" / "live_semantic_cases.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
