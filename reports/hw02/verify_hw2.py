import json
from pathlib import Path

from fastapi.testclient import TestClient

from main import app
from src.agent_graph import PlannerOutput, build_graph


BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "reports" / "hw02" / "verification.json"


def main():
    results = []

    try:
        client = TestClient(app)

        response = client.get("/api/inspections")

        results.append({
            "check": "GET inspections",
            "passed": response.status_code == 200
        })

        response = client.get(
            "/api/inspections?search=San Jose"

        )

        results.append({
            "check": "Search endpoint",
            "passed": response.status_code == 200
        })

        valid_output = {
            "tags": [
                "FoodSafety",
                "KitchenCheck",
                "SanitationCheck"
            ],
            "summary": "Restaurant inspection checks food safety and sanitation."
        }

        PlannerOutput.model_validate(valid_output)

        results.append({
            "check": "Valid Planner output",
            "passed": True
        })

        invalid_output = {
            "tags": [
                "x",
                "y"
            ],
            "summary": "Invalid output"
        }

        try:
            PlannerOutput.model_validate(invalid_output)
            validation_failed = False
        except Exception:
            validation_failed = True

        results.append({
            "check": "Invalid Planner output rejected",
            "passed": validation_failed
        })

        graph = build_graph()

        state = {
            "title": "Local Restaurant Inspection",
            "content": "A local restaurant inspection checked kitchen conditions, food safety practices, sanitation, and compliance with restaurant inspection requirements.",
            "task": "Create three topical tags and a short summary.",
            "planner_proposal": {},
            "reviewer_feedback": {},
            "turn_count": 0,
            "max_turns": 2,
            "force_reviewer_failure": False,
            "force_invalid_first": False
        }

        final_state = graph.invoke(state)

        graph_passed = (
            final_state.get(
                "reviewer_feedback",
                {}
            ).get(
                "approved",
                False
            )
            and final_state.get(
                "turn_count",
                0
            ) >= 1
        )

        results.append({
            "check": "LangGraph normal run",
            "passed": graph_passed
        })

        overall_passed = all(
            item["passed"]
            for item in results
        )

        verification = {
            "verification": "HW2 self-check",
            "overall_passed": overall_passed,
            "checks": results
        }

    except Exception as error:

        verification = {
            "verification": "HW2 self-check",
            "overall_passed": False,
            "error": str(error),
            "checks": results
        }

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            verification,
            f,
            indent=2
        )

    print(
        json.dumps(
            verification,
            indent=2
          )  
        )


if __name__ == "__main__":
    main()