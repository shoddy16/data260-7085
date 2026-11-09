"""Record bounded repair, lesson reuse, rejection, and variant results."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from hw9_agents import EvaluatorAgent, SelfImprovingSystem, run_variants

ROOT = Path(__file__).resolve().parent
REFERENCE = ROOT / "data" / "hw9" / "reference_data.json"


class AlwaysReviseEvaluator(EvaluatorAgent):
    def evaluate(self, question, answer):
        result = super().evaluate(question, answer)
        result.result = "REVISE"
        result.correct = False
        result.feedback = "Use this verified fact: rejected lesson"
        return result


def main():
    with tempfile.TemporaryDirectory(dir=ROOT / "reports") as directory:
        lessons = Path(directory) / "lessons.json"
        lessons.write_text("[]", encoding="utf-8")
        system = SelfImprovingSystem(REFERENCE, lessons)
        question = "Which restaurants scored below 70?"
        system.answerer.forced_first_answers = {question: "incorrect answer"}
        first = system.run(question)
        saved_after_first = json.loads(lessons.read_text(encoding="utf-8"))
        system.run(question)
        saved_after_second = json.loads(lessons.read_text(encoding="utf-8"))
        rejected = SelfImprovingSystem(REFERENCE, Path(directory) / "rejected.json")
        rejected.evaluator = AlwaysReviseEvaluator(REFERENCE)
        rejected.answerer.forced_first_answers = {question: "incorrect answer"}
        rejected_result = rejected.run(question)
        variants = run_variants([question, "Which restaurant scored above 90?"], REFERENCE, Path(directory) / "variants.json")
        payload = {
            "bounded_repair": first,
            "lesson_count_after_repair": len(saved_after_first),
            "lesson_use_count_after_reuse": saved_after_second[0]["use_count"],
            "rejected_lesson_result": rejected_result,
            "rejected_lesson_file_exists": (Path(directory) / "rejected.json").exists(),
            "variants": variants,
        }
        print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
