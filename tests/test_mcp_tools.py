import os
import sys
import unittest
from unittest.mock import AsyncMock
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite://")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from domain.inspection_tools import InspectionTools, SQLInspectionRepository
from database.database import Base
from models.models import Inspection, Restaurant
from meals_server import MealDBClient


class FixtureRepository:
    def search(self, query, limit):
        return [{"id": 7, "restaurant": "Harbor Cafe", "category": "Routine"}][:limit]

    def detail(self, inspection_id):
        if inspection_id != 7:
            return None
        return {"id": 7, "restaurant": "Harbor Cafe", "score": 95}

    def aggregate(self, group_by):
        return [{"group": group_by, "inspection_count": 1, "average_score": 95.0}]


class DomainToolContractTests(unittest.TestCase):
    def setUp(self):
        self.tools = InspectionTools(FixtureRepository())

    def test_search_valid_envelope(self):
        result = self.tools.search("Harbor", 5)
        self.assertEqual(result["ok"], True)
        self.assertIsNone(result["error"])
        self.assertEqual(result["data"][0]["id"], 7)

    def test_search_rejects_blank_query(self):
        result = self.tools.search("   ")
        self.assertEqual(result, {"ok": False, "data": None, "error": "query must be a non-empty string"})

    def test_detail_lookup_valid_envelope(self):
        result = self.tools.detail_lookup(7)
        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["score"], 95)

    def test_detail_lookup_rejects_invalid_id(self):
        result = self.tools.detail_lookup(0)
        self.assertEqual(result["ok"], False)
        self.assertIsNone(result["data"])
        self.assertIn("positive integer", result["error"])

    def test_aggregate_valid_envelope(self):
        result = self.tools.aggregate("category")
        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"][0]["inspection_count"], 1)

    def test_aggregate_rejects_unsupported_group(self):
        result = self.tools.aggregate("email")
        self.assertEqual(result["ok"], False)
        self.assertIsNone(result["data"])
        self.assertIn("group_by", result["error"])


class SQLSearchTests(unittest.TestCase):
    def test_search_terms_can_match_across_restaurant_and_location_fields(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        sessions = sessionmaker(bind=engine)
        with sessions() as db:
            restaurant = Restaurant(name="Restaurant 1", location="Mountain View, CA", code="s7085-r-12345678")
            db.add(restaurant)
            db.flush()
            db.add(Inspection(
                restaurant_id=restaurant.id,
                inspection_code="s7085-i-00000001",
                score=100,
                restaurantName=restaurant.name,
                location=restaurant.location,
                email="fixture@example.com",
                description="Food safety inspection.",
                category="Sanitation",
            ))
            db.commit()
        results = SQLInspectionRepository(sessions).search("Find inspections for Restaurant 1 in Mountain View", 5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["restaurant"], "Restaurant 1")
        engine.dispose()


class MealToolContractTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = MealDBClient(base_url="https://fixture.invalid")
        self.client._get = AsyncMock()
        self.recipe = {
            "idMeal": "52772",
            "strMeal": "Teriyaki Chicken Casserole",
            "strMealThumb": "https://example.invalid/meal.jpg",
            "strArea": "Japanese",
            "strCategory": "Chicken",
            "strInstructions": "Bake until cooked.",
            "strSource": "https://example.invalid/source",
            "strYoutube": "https://example.invalid/video",
            "strIngredient1": "chicken",
            "strMeasure1": "1 lb",
        }

    async def test_name_search_card_shape_and_limit(self):
        self.client._get.return_value = {"meals": [self.recipe, self.recipe]}
        result = await self.client.search_meals_by_name("Teriyaki", 1)
        self.assertEqual(len(result["meals"]), 1)
        self.assertEqual(
            set(result["meals"][0]),
            {"id", "name", "area", "category", "thumb"},
        )
        self.client._get.assert_awaited_once_with("search.php", {"s": "Teriyaki"})

    async def test_ingredient_search_card_shape(self):
        self.client._get.return_value = {"meals": [self.recipe]}
        result = await self.client.meals_by_ingredient("chicken", 4)
        self.assertEqual(set(result["meals"][0]), {"id", "name", "thumb"})

    async def test_random_recipe_details_shape(self):
        self.client._get.return_value = {"meals": [self.recipe]}
        result = await self.client.random_meal()
        self.assertEqual(
            set(result),
            {"id", "name", "category", "area", "instructions", "image", "source", "youtube", "ingredients"},
        )
        self.assertEqual(result["ingredients"], [{"name": "chicken", "measure": "1 lb"}])

    async def test_id_lookup_and_empty_results(self):
        self.client._get.return_value = {"meals": [self.recipe]}
        result = await self.client.meal_details(52772)
        self.client._get.assert_awaited_with("lookup.php", {"i": "52772"})
        self.assertEqual(result["id"], "52772")
        self.client._get.return_value = {"meals": None}
        empty = await self.client.search_meals_by_name("Unknown")
        self.assertEqual(empty, {"meals": [], "message": "No matches"})

    async def test_bad_search_input_is_rejected_before_network_call(self):
        with self.assertRaises(ValueError):
            await self.client.search_meals_by_name(" ", 5)
        self.client._get.assert_not_awaited()


if __name__ == "__main__":
    unittest.main(verbosity=2)
