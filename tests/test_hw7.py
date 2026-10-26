import json
import shutil
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from database.database import Base, engine
from hw7_agent import ScriptedActionModel, run_agent, run_reflexion
from hw7_bikeshare import calculator, csv_sql
from hw7_filetools import confirm_bash, edit_file, glob_files, is_destructive, read_file, search_in_files, write_file
from hw7_seed import seed_users
from main import app


class HW7ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        seed_users()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        Base.metadata.drop_all(bind=engine)

    def token(self, username):
        response = self.client.post("/auth/login", data={"username": username, "password": username})
        self.assertEqual(response.status_code, 200)
        return response.json()["access_token"]

    def test_login_me_and_role_boundaries(self):
        self.assertEqual(
            self.client.post("/auth/login", data={"username": "reader", "password": "bad"}).status_code, 401
        )
        self.assertEqual(self.client.get("/auth/me").status_code, 401)
        reader = self.token("reader")
        writer = self.token("writer")
        moderator = self.token("moderator")
        self.assertEqual(
            self.client.get("/auth/me", headers={"Authorization": f"Bearer {reader}"}).json()["role"], "reader"
        )
        payload = {
            "restaurantName": "HW7 Cafe",
            "location": "SJ",
            "email": "hw7@example.com",
            "description": "clean",
            "category": "food",
        }
        self.assertEqual(
            self.client.post("/inspections/", json=payload, headers={"Authorization": f"Bearer {reader}"}).status_code,
            403,
        )
        created = self.client.post("/inspections/", json=payload, headers={"Authorization": f"Bearer {writer}"})
        self.assertEqual(created.status_code, 201)
        inspection_id = created.json()["id"]
        self.assertEqual(
            self.client.get("/inspections/", headers={"Authorization": f"Bearer {reader}"}).status_code, 200
        )
        self.assertEqual(
            self.client.delete(
                f"/inspections/{inspection_id}", headers={"Authorization": f"Bearer {writer}"}
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.delete(
                f"/inspections/{inspection_id}", headers={"Authorization": f"Bearer {moderator}"}
            ).status_code,
            204,
        )


class HW7ToolTests(unittest.TestCase):
    def test_agent_tool_role_and_repair(self):
        result = run_agent(
            "find restaurant",
            model=ScriptedActionModel(
                [{"tool": "search", "inputs": {"query": "restaurant", "limit": 1}}, {"final": "done"}]
            ),
            tool_executor=lambda *_: json.dumps({"ok": True, "data": []}),
        )
        self.assertEqual(result["stop_reason"], "success")
        self.assertEqual(result["tool_call_count"], 1)
        repaired = run_agent(
            "find",
            model=ScriptedActionModel([{"tool": "bogus", "inputs": {}}, {"final": "repaired"}]),
            tool_executor=lambda *_: "{}",
        )
        self.assertEqual(repaired["repairs"], 1)

    def test_reflexion_and_mrkl(self):
        model = ScriptedActionModel(
            [
                {"tool": "search", "inputs": {"query": "restaurant"}},
                {"tool": "detail_lookup", "inputs": {"inspection_id": 1}},
                {"final": "done"},
            ]
        )
        result = run_reflexion("A", [model])
        self.assertEqual(result["stop_reason"], "success")
        self.assertTrue(csv_sql("duration_minutes\n10\n", "SELECT COUNT(*) AS n FROM trips")["success"])
        self.assertFalse(csv_sql("duration_minutes\n10\n", "DELETE FROM trips")["success"])
        self.assertEqual(calculator("2 + 3 * 4")["data"]["value"], 20.0)

    def test_file_tools_and_gate(self):
        parent = Path.cwd() / "tmp" / "hw7_test_tmp"
        parent.mkdir(exist_ok=True)
        root = parent / "sandbox"
        root.mkdir(parents=True, exist_ok=True)
        try:
            write_file(root / "one.py", "print('DEBUG')\n", root)
            write_file(root / "two.py", "print('OK')\n", root)
            self.assertEqual(len(glob_files("*.py", root)), 2)
            self.assertEqual(len(search_in_files("DEBUG", root, "*.py")), 1)
            self.assertIn("DEBUG", read_file(root / "one.py", root, 1))
            self.assertIn("OK", edit_file(root / "two.py", "OK", "DEBUG", root))
        finally:
            shutil.rmtree(root, ignore_errors=True)
        self.assertFalse(confirm_bash("rm -rf sandbox", False)["allowed"])
        self.assertTrue(confirm_bash('python -c "print(1)"', False)["allowed"])
        self.assertTrue(is_destructive("sudo chmod 777 /tmp/x"))


if __name__ == "__main__":
    unittest.main()
