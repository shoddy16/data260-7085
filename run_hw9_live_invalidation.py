"""Demonstrate stale-answer protection with the real MySQL row and Redis."""

from __future__ import annotations

import json
import os
from urllib.parse import quote_plus

import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from hw9_cache import EmbeddingProvider, SemanticCache
from models.models import Restaurant
from routers.hw9 import query_signature


def main():
    database = os.getenv("MYSQL_DATABASE", "db_session_basede26")
    url = f"mysql+pymysql://root:{quote_plus(os.environ['MYSQL_PWD'])}@127.0.0.1:3306/{database}"
    engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    sessions = sessionmaker(bind=engine)
    db = sessions()
    redis_client = redis.Redis(host="127.0.0.1", port=6380, decode_responses=True)
    cache = SemanticCache(redis_client, provider=EmbeddingProvider(lambda _: [1.0, 0.0]))
    question = "HW9 live location for restaurant 1"
    restaurant = db.get(Restaurant, 1)
    if restaurant is None:
        raise RuntimeError("Expected live HW9 restaurant row was not found")
    original = restaurant.location
    try:
        restaurant.location = "San Jose"
        db.commit()
        first = cache.answer(question, query_signature(question), lambda: f"location={restaurant.location}", restaurant_id=1)
        stale_before_invalidation = cache.answer(question, query_signature(question), lambda: f"location={restaurant.location}", restaurant_id=1)
        restaurant.location = "HW9-Updated-City"
        db.commit()
        stale_after_database_update = cache.answer(question, query_signature(question), lambda: f"location={restaurant.location}", restaurant_id=1)
        cache.invalidate_restaurant(1)
        fresh_after_invalidation = cache.answer(question, query_signature(question), lambda: f"location={restaurant.location}", restaurant_id=1)
        print(json.dumps({
            "first": first.__dict__,
            "stale_before_invalidation": stale_before_invalidation.__dict__,
            "stale_after_database_update": stale_after_database_update.__dict__,
            "fresh_after_invalidation": fresh_after_invalidation.__dict__,
            "old_answer_reused_without_invalidation": stale_after_database_update.answer == first.answer,
            "updated_answer_after_invalidation": fresh_after_invalidation.answer == "location=HW9-Updated-City",
        }, indent=2))
    finally:
        restaurant.location = original
        db.commit()
        cache.invalidate_restaurant(1)
        db.close()


if __name__ == "__main__":
    main()
