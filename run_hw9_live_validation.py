"""Run live HW9 Redis/MySQL checks without storing credentials."""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import quote_plus

import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from hw9_cache import ViewCounter
from hw9_config import VIEW_KEY
from models.models import Restaurant


def main() -> None:
    password = os.environ["MYSQL_PWD"]
    database = os.getenv("MYSQL_DATABASE", "db_session_basede26")
    url = f"mysql+pymysql://root:{quote_plus(password)}@127.0.0.1:3306/{database}"
    engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    redis_client = redis.Redis(host="127.0.0.1", port=6380, decode_responses=True)
    redis_client.ping()
    result = {"redis": "PASS", "mysql": "PASS", "prefix": "s7085", "timestamp": datetime.now(timezone.utc).isoformat()}

    db = session_factory()
    try:
        restaurant = db.query(Restaurant).filter(Restaurant.code == "HW9-LIVE-7085").first()
        if restaurant is None:
            restaurant = Restaurant(name="HW9 Live Restaurant", location="San Jose", code="HW9-LIVE-7085")
            db.add(restaurant)
            db.commit()
            db.refresh(restaurant)
        restaurant_id = restaurant.id
        redis_client.delete(f"{VIEW_KEY}:{restaurant_id}")
        restaurant.views = 0
        db.commit()
        counter = ViewCounter(redis_client)
        counts = [counter.increment_restaurant_views(restaurant_id, db) for _ in range(21)]
        db.refresh(restaurant)
        result.update({
            "restaurant_id": restaurant_id,
            "counts_1_2_10_20_21": [counts[index - 1] for index in (1, 2, 10, 20, 21)],
            "database_views_after_21": restaurant.views,
            "redis_key": f"{VIEW_KEY}:{restaurant_id}",
            "tenth_sync": restaurant.views == 20,
        })
    finally:
        db.close()

    concurrent_id = restaurant_id + 1
    db = session_factory()
    try:
        concurrent = db.get(Restaurant, concurrent_id)
        if concurrent is None:
            concurrent = Restaurant(name="HW9 Concurrent Restaurant", location="San Jose", code="HW9-CONC-7085")
            db.add(concurrent)
            db.commit()
            db.refresh(concurrent)
        concurrent_id = concurrent.id
        redis_client.delete(f"{VIEW_KEY}:{concurrent_id}")
        concurrent.views = 0
        db.commit()
    finally:
        db.close()

    def increment_once(_index: int) -> int:
        local_db = session_factory()
        try:
            return ViewCounter(redis_client).increment_restaurant_views(concurrent_id, local_db)
        finally:
            local_db.close()

    with ThreadPoolExecutor(max_workers=8) as pool:
        concurrent_counts = list(pool.map(increment_once, range(20)))
    db = session_factory()
    try:
        concurrent = db.get(Restaurant, concurrent_id)
        result.update({
            "concurrent_restaurant_id": concurrent_id,
            "concurrent_redis_count": int(redis_client.get(f"{VIEW_KEY}:{concurrent_id}")),
            "concurrent_database_views": concurrent.views,
            "concurrent_unique_counts": len(set(concurrent_counts)),
        })
    finally:
        db.close()

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
