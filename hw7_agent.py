"""HW7 hand-written tool loop and bounded Reflexion extension."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from tool_executor import execute_tool

TOOLS = {"search", "detail_lookup", "aggregate"}
MAX_REPAIRS = 1


class ActionModel(Protocol):
    def next_action(self, messages: list[dict[str, Any]]) -> dict[str, Any]: ...


class AdapterActionModel:
    """Use the HW1 adapter while keeping the loop's action contract explicit."""

    def __init__(self, client=None):
        if client is None:
            from src.model_client import ModelClient

            client = ModelClient(temperature=0.0)
        self.client = client

    def next_action(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        response = self.client.complete(messages)
        content = getattr(response, "content", response)
        if isinstance(content, list):
            content = "".join(str(item) for item in content)
        parsed = json.loads(str(content))
        if not isinstance(parsed, dict):
            raise ValueError("model action must be a JSON object")
        return parsed


class ScriptedActionModel:
    def __init__(self, actions: list[dict[str, Any]]):
        self.actions = list(actions)
        self.calls = 0

    def next_action(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        self.calls += 1
        return self.actions.pop(0) if self.actions else {"final": "No further action."}


def _parse_tool_action(action: Any) -> tuple[str, dict[str, Any]]:
    if not isinstance(action, dict):
        raise ValueError("action must be an object")
    if isinstance(action.get("final"), str):
        return "__final__", {"answer": action["final"]}
    name = action.get("tool")
    inputs = action.get("inputs")
    if name not in TOOLS:
        raise ValueError(f"unknown tool: {name}")
    if not isinstance(inputs, dict):
        raise ValueError("inputs must be an object")
    required = {"search": "query", "detail_lookup": "inspection_id", "aggregate": "group_by"}[name]
    if required not in inputs:
        raise ValueError(f"missing required argument: {required}")
    return name, inputs


def run_agent(
    user_input: str,
    *,
    model: ActionModel | None = None,
    max_steps: int = 8,
    max_repairs: int = MAX_REPAIRS,
    tool_executor: Callable[[str, dict[str, Any]], str] = execute_tool,
    log_path: str | Path | None = None,
) -> dict[str, Any]:
    model = model or AdapterActionModel()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": "Use only the three domain tools. Return JSON actions. Never invent data."},
        {"role": "user", "content": user_input},
    ]
    trace: list[dict[str, Any]] = []
    repairs = 0
    tool_calls = 0
    started = time.perf_counter()
    answer = "The agent stopped before a final answer."
    stop_reason = "budget_exhausted"
    for step in range(1, max_steps + 1):
        try:
            action = model.next_action(messages)
            name, inputs = _parse_tool_action(action)
        except Exception as exc:
            trace.append({"step": step, "kind": "repair", "error": str(exc)})
            if repairs >= max_repairs:
                stop_reason = "repair_failed"
                answer = "The model could not produce a valid bounded tool action."
                break
            repairs += 1
            messages.append({"role": "tool", "name": "validation", "content": json.dumps({"error": str(exc)})})
            messages.append({"role": "user", "content": f"Repair exactly this action problem once: {exc}"})
            continue
        if name == "__final__":
            answer = inputs["answer"]
            stop_reason = "success"
            trace.append({"step": step, "kind": "final", "answer": answer})
            break
        tool_calls += 1
        raw = tool_executor(name, inputs)
        try:
            result = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            result = {"ok": False, "error": "tool returned invalid JSON"}
        trace.append({"step": step, "kind": "tool", "tool": name, "inputs": inputs, "result": result})
        messages.append({"role": "assistant", "content": json.dumps(action)})
        messages.append({"role": "tool", "name": name, "content": json.dumps(result, ensure_ascii=False)})
    summary = {
        "answer": answer,
        "stop_reason": stop_reason,
        "step_count": len(trace),
        "tool_call_count": tool_calls,
        "repairs": repairs,
        "latency_ms": round((time.perf_counter() - started) * 1000, 3),
        "trace": trace,
    }
    if log_path:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(summary, ensure_ascii=False) + "\n")
    return summary


@dataclass
class Reflection:
    evidence: str
    failure: str
    strategy: str


def verify_task(task: str, result: dict[str, Any]) -> tuple[bool, str]:
    trace = result.get("trace", [])
    if task == "A":
        ok = [x for x in trace if x.get("kind") == "tool"]
        return len(ok) >= 2 and result["stop_reason"] == "success", "search then detail lookup required"
    if task == "B":
        return result.get("stop_reason") == "success" and result.get(
            "tool_call_count", 0
        ) >= 2, "aggregate plus supporting lookup required"
    if task == "C":
        return result.get("stop_reason") == "success" and result.get(
            "tool_call_count", 0
        ) >= 3, "search plus two detail lookups required"
    return False, "unknown verification task"


def run_reflexion(task: str, attempts: list[ActionModel], max_retries: int = 2) -> dict[str, Any]:
    reflections: list[Reflection] = []
    for retry, model in enumerate(attempts[: max_retries + 1]):
        result = run_agent(task, model=model, max_steps=8)
        passed, reason = verify_task(task, result)
        if passed:
            result.update(
                {"reflexion_retries": retry, "reflections": [r.__dict__ for r in reflections], "stop_reason": "success"}
            )
            return result
        if retry >= max_retries:
            result.update(
                {
                    "reflexion_retries": retry,
                    "reflections": [r.__dict__ for r in reflections],
                    "stop_reason": "human_review",
                }
            )
            return result
        reflections.append(
            Reflection(
                evidence=json.dumps(result.get("trace", [])[-2:]),
                failure=reason,
                strategy="use the missing distinct tool call before answering",
            )
        )
    return {
        "stop_reason": "human_review",
        "reflexion_retries": max_retries,
        "reflections": [r.__dict__ for r in reflections],
    }
