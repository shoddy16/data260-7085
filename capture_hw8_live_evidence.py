"""Capture reproducible live Docker/Kafka evidence without fabricating output."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "reports" / "hw08" / "evidence"


def run(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    commands = {
        "docker_ps": ["docker", "compose", "-f", "docker-compose.hw8.yml", "ps"],
        "topics": ["docker", "exec", "s7085-kafka", "/opt/kafka/bin/kafka-topics.sh", "--bootstrap-server", "localhost:9092", "--list"],
        "tasks_description": ["docker", "exec", "s7085-kafka", "/opt/kafka/bin/kafka-topics.sh", "--bootstrap-server", "localhost:9092", "--describe", "--topic", "s7085_tasks"],
        "service_logs": ["docker", "compose", "-f", "docker-compose.hw8.yml", "logs", "--tail", "80", "api", "worker", "planner", "writer", "reviewer"],
        "final_message": ["docker", "exec", "s7085-kafka", "/opt/kafka/bin/kafka-console-consumer.sh", "--bootstrap-server", "localhost:9092", "--topic", "s7085_final", "--from-beginning", "--group", "hw8-evidence-capture", "--max-messages", "1", "--timeout-ms", "5000"],
    }
    results = {name: run(command) for name, command in commands.items()}
    timestamp = datetime.now(timezone.utc).isoformat()
    for name, result in results.items():
        (EVIDENCE / f"{name}.txt").write_text(
            f"Captured UTC: {timestamp}\nCommand: {result['command']}\nExit: {result['returncode']}\n\n{result['stdout']}\n{result['stderr']}",
            encoding="utf-8",
        )
    (EVIDENCE / "live_capture.json").write_text(json.dumps({"captured_utc": timestamp, "results": results}, indent=2), encoding="utf-8")
    return 0 if all(result["returncode"] == 0 for result in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
