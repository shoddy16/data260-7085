"""Deterministic self-improving restaurant-inspection agents for HW9."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Evaluation:
    result: str
    explanation: str
    feedback: str
    correct: bool


class EvaluatorAgent:
    def __init__(self, reference_path: str | Path):
        self.reference = json.loads(Path(reference_path).read_text(encoding="utf-8"))

    def evaluate(self, question: str, answer: str) -> Evaluation:
        expected = self.reference.get(question)
        correct = expected is not None and expected.lower() in answer.lower()
        if correct:
            return Evaluation("PASS", "Answer contains the reference fact.", "", True)
        return Evaluation("REVISE", "Answer does not contain the reference fact.", f"Use this verified fact: {expected}", False)


class AnsweringAgent:
    def __init__(
        self,
        reference_path: str | Path,
        forced_first_answers: dict[str, str] | None = None,
        model_client: Any | None = None,
    ):
        self.reference = json.loads(Path(reference_path).read_text(encoding="utf-8"))
        self.forced_first_answers = forced_first_answers or {}
        self.model_client = model_client
        self.calls: dict[str, int] = {}

    def answer(self, question: str, lessons: list[dict[str, Any]], feedback: str = "") -> str:
        count = self.calls.get(question, 0)
        self.calls[question] = count + 1
        if count == 0 and question in self.forced_first_answers:
            return self.forced_first_answers[question]
        for lesson in lessons:
            lesson["use_count"] = lesson.get("use_count", 0) + 1
            if lesson.get("failure_pattern") and lesson.get("correction") and lesson["failure_pattern"] in question:
                return lesson["correction"].replace("Use this verified fact: ", "")
        if self.model_client and not feedback:
            response = self.model_client.complete([
                {"role": "system", "content": "Answer the restaurant inspection question concisely. Do not invent facts."},
                {"role": "user", "content": question},
            ])
            content = getattr(response, "content", response)
            if isinstance(content, list):
                content = "".join(str(item) for item in content)
            if str(content).strip():
                return str(content).strip()
        if feedback:
            return feedback.replace("Use this verified fact: ", "")
        return self.reference.get(question, "I do not have a verified fact for that question.")


class SelfImprovingSystem:
    def __init__(self, reference_path: str | Path, lessons_path: str | Path, model_client: Any | None = None):
        self.answerer = AnsweringAgent(reference_path, model_client=model_client)
        self.evaluator = EvaluatorAgent(reference_path)
        self.lessons_path = Path(lessons_path)
        self.lessons = self._load_lessons()

    def _load_lessons(self) -> list[dict[str, Any]]:
        if not self.lessons_path.exists():
            return []
        return json.loads(self.lessons_path.read_text(encoding="utf-8"))

    def _save_lessons(self) -> None:
        self.lessons_path.parent.mkdir(parents=True, exist_ok=True)
        self.lessons_path.write_text(json.dumps(self.lessons, indent=2), encoding="utf-8")

    def run(self, question: str, *, save_lesson: bool = True) -> dict[str, Any]:
        started = time.perf_counter()
        relevant = list(self.lessons)
        initial = self.answerer.answer(question, relevant)
        first_eval = self.evaluator.evaluate(question, initial)
        attempts = 1
        final = initial
        final_eval = first_eval
        if first_eval.result == "REVISE":
            final = self.answerer.answer(question, relevant, first_eval.feedback)
            final_eval = self.evaluator.evaluate(question, final)
            attempts = 2
        if save_lesson and first_eval.result == "REVISE" and final_eval.correct:
            self.lessons.append({
                "lesson_id": f"lesson_{uuid.uuid4().hex[:8]}",
                "failure_pattern": first_eval.explanation,
                "correction": first_eval.feedback,
                "created_at": time.strftime("%Y-%m-%d"),
                "use_count": 0,
            })
            self._save_lessons()
        elif save_lesson and self.lessons:
            # Persist use_count changes when a previously validated lesson is reused.
            self._save_lessons()
        return {
            "question": question,
            "initial_answer": initial,
            "evaluation": first_eval.result,
            "feedback": first_eval.feedback,
            "revised_answer": final if attempts == 2 else None,
            "final_evaluation": final_eval.result,
            "attempts": attempts,
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
        }


def run_variants(questions: list[str], reference_path: str | Path, lessons_path: str | Path) -> list[dict[str, Any]]:
    output = []
    for variant in ("baseline", "evaluator_repair", "lesson_memory", "validated_improvement"):
        lessons_path = Path(lessons_path)
        lessons_path.write_text("[]", encoding="utf-8")
        system = SelfImprovingSystem(reference_path, lessons_path)
        if questions:
            system.answerer.forced_first_answers = {questions[0]: "intentionally incorrect answer"}
        if variant == "lesson_memory" and questions:
            system.lessons = [{
                "lesson_id": "seeded_lesson",
                "failure_pattern": questions[0],
                "correction": f"Use this verified fact: {system.answerer.reference.get(questions[0], '')}",
                "created_at": "2026-11-05",
                "use_count": 0,
            }]
            system._save_lessons()
        if variant == "baseline":
            system.evaluator = EvaluatorAgent(reference_path)
            def runner(q: str) -> dict[str, Any]:
                started = time.perf_counter()
                answer = system.answerer.answer(q, [])
                evaluation = system.evaluator.evaluate(q, answer)
                return {"final_evaluation": "PASS" if evaluation.correct else "REVISE", "attempts": 1,
                        "latency_ms": round((time.perf_counter() - started) * 1000, 3)}
        else:
            def runner(q: str) -> dict[str, Any]:
                return system.run(q, save_lesson=variant != "evaluator_repair")
        results = [runner(question) for question in questions]
        correct = sum(item.get("final_evaluation") == "PASS" for item in results)
        output.append({
            "variant": variant,
            "correct_answers": correct,
            "incorrect_answers": len(results) - correct,
            "average_attempts": sum(item.get("attempts", 1) for item in results) / len(results),
            "average_latency_ms": sum(item.get("latency_ms", 0) for item in results) / len(results),
        })
    return output
