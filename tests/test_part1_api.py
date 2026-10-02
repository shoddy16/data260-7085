"""API smoke coverage for the HW5 Restaurant/Inspection relationship."""

import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
os.environ["DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402


class PartOneApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_restaurant_and_inspection_crud_relationship_and_constraints(self):
        create_restaurant = self.client.post(
            "/restaurants/",
            json={"name": "Harbor Cafe", "location": "San Jose"},
        )
        self.assertEqual(create_restaurant.status_code, 201)
        restaurant = create_restaurant.json()
        self.assertRegex(restaurant["code"], r"^s7085-r-[a-f0-9]{8}$")
        self.assertIn("created_at", restaurant)
        restaurant_id = restaurant["id"]

        duplicate_code = self.client.post(
            "/restaurants/",
            json={"name": "Duplicate", "location": "San Jose", "code": restaurant["code"]},
        )
        self.assertEqual(duplicate_code.status_code, 409)
        invalid_code = self.client.post(
            "/restaurants/",
            json={"name": "Bad Code", "location": "San Jose", "code": "wrong-format"},
        )
        self.assertEqual(invalid_code.status_code, 422)

        list_response = self.client.get("/restaurants/?skip=0&limit=1")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)
        self.assertEqual(self.client.get(f"/restaurants/{restaurant_id}").status_code, 200)

        inspection_response = self.client.post(
            "/inspections/",
            json={
                "restaurant_id": restaurant_id,
                "restaurantName": restaurant["name"],
                "location": restaurant["location"],
                "email": "owner@example.com",
                "description": "Routine food-safety inspection.",
                "category": "Routine",
                "score": 96,
            },
        )
        self.assertEqual(inspection_response.status_code, 201)
        inspection = inspection_response.json()
        self.assertEqual(inspection["restaurant_id"], restaurant_id)
        self.assertEqual(inspection["score"], 96)
        self.assertEqual(inspection["restaurant"]["id"], restaurant_id)
        inspection_id = inspection["id"]

        related = self.client.get(f"/restaurants/{restaurant_id}/inspections")
        self.assertEqual(related.status_code, 200)
        self.assertEqual([row["id"] for row in related.json()], [inspection_id])

        updated_restaurant = self.client.put(
            f"/restaurants/{restaurant_id}", json={"name": "Harbor Cafe Updated"}
        )
        self.assertEqual(updated_restaurant.status_code, 200)
        updated_linked_inspections = self.client.get(
            f"/restaurants/{restaurant_id}/inspections"
        ).json()
        self.assertEqual(
            updated_linked_inspections[0]["restaurantName"],
            "Harbor Cafe Updated",
        )
        updated_inspection = self.client.put(
            f"/inspections/{inspection_id}", json={"score": 90}
        )
        self.assertEqual(updated_inspection.status_code, 200)
        self.assertEqual(updated_inspection.json()["score"], 90)
        self.assertEqual(updated_inspection.json()["restaurantName"], "Harbor Cafe Updated")

        self.assertEqual(self.client.delete(f"/restaurants/{restaurant_id}").status_code, 409)
        self.assertEqual(self.client.delete(f"/inspections/{inspection_id}").status_code, 204)
        self.assertEqual(self.client.delete(f"/restaurants/{restaurant_id}").status_code, 204)
        self.assertEqual(self.client.get("/restaurants/99999").status_code, 404)
        self.assertEqual(
            self.client.put("/restaurants/99999", json={"name": "Missing"}).status_code,
            404,
        )

    def test_legacy_inspection_create_auto_links_a_restaurant(self):
        response = self.client.post(
            "/inspections/",
            json={
                "restaurantName": "Legacy Diner",
                "location": "San Jose",
                "email": "legacy@example.com",
                "description": "Legacy client payload.",
                "category": "Routine",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.json()["restaurant_id"])
        self.assertEqual(response.json()["score"], 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
