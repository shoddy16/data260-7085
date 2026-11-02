"""Run the real Kafka RPC CREATE/GET flow and save its responses."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from kafka_rpc import KafkaRPC


async def main() -> None:
    rpc = KafkaRPC()
    created = await rpc.request(
        "CREATE_ENTITY",
        {
            "restaurantName": "Live Evidence Cafe",
            "location": "San Jose",
            "email": "live@example.com",
            "description": "live Kafka RPC evidence",
            "category": "restaurant",
            "score": 91,
        },
    )
    fetched = await rpc.request("GET_ENTITY", {"entity_id": created["entity_id"]})
    result = {"captured_utc": datetime.now(timezone.utc).isoformat(), "create": created, "get": fetched}
    path = Path("/app/reports/hw08/evidence/live_entity.json")
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
