import csv
import json
import subprocess
import time
from pathlib import Path


INPUT_FILE = Path("reports/hw01/cases/nondeterminism_input.json")
RAW_DIR = Path("reports/hw01/raw")
RAW_JSON = RAW_DIR / "nondeterminism_results.json"
RAW_CSV = RAW_DIR / "nondeterminism_results.csv"


def run_once(temperature, run_number):
    data = json.loads(INPUT_FILE.read_text(encoding="utf-8-sig"))

    command = [
        str(Path(".venv/Scripts/python.exe")),
        "agent_demo.py",
        "--title",
        data["title"],
        "--content",
        data["content"],
        "--temperature",
        str(temperature),
    ]

    start = time.perf_counter()

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    latency_ms = (time.perf_counter() - start) * 1000

    if result.returncode != 0:
        raise RuntimeError(
            f"Run failed.\n"
            f"Temperature: {temperature}\n"
            f"Run: {run_number}\n\n"
            f"STDERR:\n{result.stderr}\n\n"
            f"STDOUT:\n{result.stdout}"
        )

    stdout = result.stdout

    marker = "========== FINALIZED OUTPUT =========="

    if marker not in stdout:
        raise RuntimeError(
            f"FINALIZED OUTPUT was not found.\n\n{stdout}"
        )

    final_text = stdout.split(marker, 1)[1].strip()

    decoder = json.JSONDecoder()
    final_output, _ = decoder.raw_decode(final_text)

    record = {
        "run": run_number,
        "temperature": temperature,
        "latency_ms": round(latency_ms, 2),
        "planner_output": None,
        "reviewer_output": None,
        "final_output": final_output,
        "raw_stdout": stdout,
    }

    
    planner_marker = "========== PLANNER OUTPUT =========="

    if planner_marker in stdout:
        planner_text = stdout.split(planner_marker, 1)[1]

        if "========== REVIEWER OUTPUT ==========" in planner_text:
            planner_text = planner_text.split(
                "========== REVIEWER OUTPUT ==========",
                1
            )[0].strip()

        try:
            record["planner_output"], _ = decoder.raw_decode(planner_text)
        except json.JSONDecodeError:
            pass

    
    reviewer_marker = "========== REVIEWER OUTPUT =========="

    if reviewer_marker in stdout:
        reviewer_text = stdout.split(reviewer_marker, 1)[1]

        if marker in reviewer_text:
            reviewer_text = reviewer_text.split(marker, 1)[0].strip()

        try:
            record["reviewer_output"], _ = decoder.raw_decode(reviewer_text)
        except json.JSONDecodeError:
            pass

    return record


def save_results(results):
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Complete structured JSON
    RAW_JSON.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    
    with RAW_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "run",
                "temperature",
                "latency_ms",
                "tags",
                "summary",
            ],
        )

        writer.writeheader()

        for result in results:
            final_output = result["final_output"]

            writer.writerow({
                "run": result["run"],
                "temperature": result["temperature"],
                "latency_ms": result["latency_ms"],
                "tags": " | ".join(final_output.get("tags", [])),
                "summary": final_output.get("summary", ""),
            })


def main():
    results = []

    print("=" * 60)
    print("PART 3 - NON-DETERMINISM EXPERIMENT")
    print("=" * 60)
    print()
    print("Fixed input:")
    print(INPUT_FILE)
    print()
    print("Temperature 0.7: 20 runs")
    print("Temperature 0.0: 20 runs")
    print()
    print("Starting experiment...")
    print()

    for temperature in [0.7, 0.0]:

        print(f"--- Temperature {temperature} ---")

        for run_number in range(1, 21):

            print(
                f"Run {run_number:02d}/20 "
                f"(temperature={temperature})..."
            )

            record = run_once(
                temperature,
                run_number,
            )

            results.append(record)

        print()

    save_results(results)

    print("=" * 60)
    print("EXPERIMENT COMPLETE")
    print("=" * 60)
    print(f"Total runs: {len(results)}")
    print()
    print(f"Raw JSON: {RAW_JSON}")
    print(f"Raw CSV:  {RAW_CSV}")
    print()


if __name__ == "__main__":
    main()