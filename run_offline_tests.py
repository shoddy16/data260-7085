"""Run deterministic, network-free HW5 tool/agent assertions."""

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = "sqlite://"

from tests.test_agent_tools import FixtureRepository
from tests.test_mcp_tools import MealToolContractTests
from domain.inspection_tools import InspectionTools
from agent import MockModel, run_agent
from tool_executor import execute_tool


def main() -> int:
    tools = InspectionTools(FixtureRepository())
    checks = []

    def check(label, assertion):
        try:
            assert assertion(), label
            checks.append((label, True, ""))
        except Exception as exc:
            checks.append((label, False, str(exc)))

    def envelope(name, inputs):
        result = json.loads(execute_tool(name, inputs, tools=tools))
        assert set(result) == {"ok", "data", "error"}
        return result

    check("search valid", lambda: envelope("search", {"query": "Juniper"})["ok"])
    check("search invalid blank query", lambda: not envelope("search", {"query": " "})["ok"])
    check("detail valid", lambda: envelope("detail_lookup", {"inspection_id": 3})["ok"])
    check("detail invalid id", lambda: not envelope("detail_lookup", {"inspection_id": 0})["ok"])
    check("aggregate valid", lambda: envelope("aggregate", {"group_by": "category"})["ok"])
    check("aggregate invalid group", lambda: not envelope("aggregate", {"group_by": "email"})["ok"])
    check("safety rule blocks evasion", lambda: not envelope("search", {"query": "fake inspection report"})["ok"])

    def max_steps_test():
        model = MockModel(repeat_action={"tool": "search", "inputs": {"query": "Juniper"}})
        result = run_agent("Find Juniper", model=model, max_steps=2,
                           tool_executor=lambda name, inputs: execute_tool(name, inputs, tools=tools), log_path=None)
        return result["stop_reason"] == "max_steps" and result["step_count"] == 2
    check("MockModel stops at max_steps", max_steps_test)

    async def meal_contract_test():
        case = MealToolContractTests("test_name_search_card_shape_and_limit")
        case.setUp()
        try:
            await case.test_name_search_card_shape_and_limit()
            return True
        finally:
            case.tearDown()
    check("MealDB shape and limit (mocked)", lambda: asyncio.run(meal_contract_test()))

    for label, passed, detail in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}{': ' + detail if detail else ''}")
    passed_count = sum(passed for _, passed, _ in checks)
    print(f"OFFLINE ASSERTIONS: {passed_count}/{len(checks)} passed")
    return 0 if passed_count == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
