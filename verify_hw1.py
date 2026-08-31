import json
from pathlib import Path

ROOT = Path(__file__).parent
REPORT = ROOT / "reports" / "hw01"

checks = []


def check(name, condition, details=""):
    checks.append({
        "check": name,
        "passed": bool(condition),
        "details": details
    })



required_files = [
    "agent_demo.py",
    "hw1_client.py",
    "review_sample.py",
    "run_experiment.py",
    "Dockerfile",
    "DOMAIN_SCHEMA.md",
    "index.html",
    "script.js",
    "AGENT.md",
    "src/model_client.py",
]

for file_name in required_files:
    path = ROOT / file_name
    check(
        f"Required file exists: {file_name}",
        path.exists(),
        str(path)
    )



required_report_files = [
    REPORT / "cases" / "nondeterminism_input.json",
    REPORT / "raw" / "nondeterminism_results.json",
    REPORT / "raw" / "nondeterminism_results.csv",
    REPORT / "METRICS.md",
    REPORT / "AI_USE.md",
]

for path in required_report_files:
    check(
        f"HW01 artifact exists: {path.relative_to(ROOT)}",
        path.exists(),
        str(path)
    )



results_file = REPORT / "raw" / "nondeterminism_results.json"

if results_file.exists():
    try:
        results = json.loads(
            results_file.read_text(encoding="utf-8-sig")
        )

        check(
            "Nondeterminism JSON is valid",
            isinstance(results, list),
            f"Loaded {len(results)} records"
        )

        check(
            "Exactly 40 nondeterminism runs",
            len(results) == 40,
            f"Found {len(results)} runs"
        )

        temperatures = {
            item.get("temperature")
            for item in results
        }

        check(
            "Both temperatures are present",
            temperatures == {0.0, 0.7},
            f"Temperatures found: {sorted(temperatures)}"
        )

        check(
            "Each run contains latency",
            all(
                isinstance(item.get("latency_ms"), (int, float))
                for item in results
            ),
            "All runs contain numeric latency_ms"
        )

        check(
            "Each run contains final output",
            all(
                isinstance(item.get("final_output"), dict)
                for item in results
            ),
            "All runs contain final_output"
        )

        check(
            "Each final output has exactly 3 tags",
            all(
                isinstance(item["final_output"].get("tags"), list)
                and len(item["final_output"]["tags"]) == 3
                for item in results
            ),
            "All 40 runs contain exactly 3 tags"
        )

    except Exception as exc:
        check(
            "Nondeterminism JSON can be parsed",
            False,
            repr(exc)
        )



input_file = REPORT / "cases" / "nondeterminism_input.json"

if input_file.exists():
    try:
        input_data = json.loads(
            input_file.read_text(encoding="utf-8-sig")
        )

        check(
            "Fixed nondeterminism input is valid JSON",
            isinstance(input_data, dict),
            "Input is a JSON object"
        )

        check(
            "Fixed input contains title and content",
            "title" in input_data and "content" in input_data,
            "Both title and content are present"
        )

    except Exception as exc:
        check(
            "Fixed input can be parsed",
            False,
            repr(exc)
        )



metrics_file = REPORT / "METRICS.md"

if metrics_file.exists():
    metrics_text = metrics_file.read_text(encoding="utf-8")

    check(
        "METRICS.md contains temperature 0.7 results",
        "52313.27" in metrics_text and "50517.81" in metrics_text,
        "Temperature 0.7 metrics found"
    )

    check(
        "METRICS.md contains temperature 0.0 results",
        "43349.38" in metrics_text and "43025.84" in metrics_text,
        "Temperature 0.0 metrics found"
    )

    check(
        "METRICS.md documents 40 runs",
        "40" in metrics_text,
        "40-run experiment documented"
    )



passed = all(item["passed"] for item in checks)

verification = {
    "assignment": "DATA 260 Homework 1",
    "status": "PASS" if passed else "FAIL",
    "total_checks": len(checks),
    "passed_checks": sum(item["passed"] for item in checks),
    "failed_checks": sum(not item["passed"] for item in checks),
    "checks": checks
}

print(json.dumps(verification, indent=2))


output_file = REPORT / "verification.json"
output_file.parent.mkdir(parents=True, exist_ok=True)
output_file.write_text(
    json.dumps(verification, indent=2),
    encoding="utf-8"
)

print()
print(f"Verification written to: {output_file}")