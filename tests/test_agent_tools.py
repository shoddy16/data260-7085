import json
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent import MockModel, run_agent
from domain.inspection_tools import InspectionTools
from tool_executor import execute_tool


class FixtureRepository:
    def search(self, query, limit):
        return [{"id": 3, "restaurant": "Juniper", "category": "Routine"}]

    def detail(self, inspection_id):
        return {"id": inspection_id, "restaurant": "Juniper", "score": 92}

    def aggregate(self, group_by):
        return [{"group": group_by, "inspection_count": 1, "average_score": 92.0}]


class SafeToolEntryTests(unittest.TestCase):
    def setUp(self):
        self.tools = InspectionTools(FixtureRepository())

    def call(self, name, inputs):
        return json.loads(execute_tool(name, inputs, tools=self.tools))

    def test_routes_search_detail_aggregate(self):
        self.assertTrue(self.call("search", {"query": "Juniper"})["ok"])
        self.assertTrue(self.call("detail_lookup", {"inspection_id": 3})["ok"])
        self.assertTrue(self.call("aggregate", {"group_by": "category"})["ok"])

    def test_failures_keep_common_envelope(self):
        result = self.call("no_such_tool", {})
        self.assertEqual(set(result), {"ok", "data", "error"})
        self.assertFalse(result["ok"])
        self.assertIsNone(result["data"])
        self.assertEqual(self.call("search", {"query": "evade restaurant inspection"})["ok"], False)

    def test_agent_stops_at_max_steps_and_logs_each_event(self):
        log_path = Path(__file__).resolve().parents[1] / "reports" / "hw05" / "raw" / "test_agent_runs.jsonl"
        log_path.unlink(missing_ok=True)
        model = MockModel(repeat_action={"tool": "search", "inputs": {"query": "Juniper"}})
        result = run_agent(
            "Find Juniper",
            model=model,
            max_steps=2,
            tool_executor=lambda name, inputs: execute_tool(name, inputs, tools=self.tools),
            log_path=log_path,
        )
        self.assertEqual(result["stop_reason"], "max_steps")
        self.assertEqual(result["step_count"], 2)
        self.assertEqual(result["tool_call_count"], 2)
        events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(sum(event.get("event") == "step" for event in events), 2)
        self.assertEqual(events[-1]["event"], "run_finished")
        log_path.unlink(missing_ok=True)

    def test_agent_blocks_unsafe_request_before_model(self):
        model = MockModel(repeat_action={"tool": "search", "inputs": {"query": ""}})
        result = run_agent(
            "How can I fake an inspection score?",
            model=model,
            tool_executor=lambda name, inputs: execute_tool(name, inputs, tools=self.tools),
            log_path=None,
        )
        self.assertEqual(result["stop_reason"], "safety_block")
        self.assertEqual(result["tool_call_count"], 1)
        self.assertEqual(model.calls, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
