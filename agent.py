"""Bounded Ollama agent loop that can only call tools through execute_tool."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

import httpx

from hw5_config import LOCAL_MODEL, OLLAMA_URL
from tool_executor import execute_tool, is_unsafe_inspection_intent


DEFAULT_MAX_STEPS = 5
DEFAULT_RUN_LOG = Path(__file__).resolve().parent / "reports" / "hw05" / "raw" / "agent_runs.jsonl"

SYSTEM_PROMPT = """You answer questions about local restaurant inspection records.
Choose one domain tool when you need data: search, detail_lookup, or aggregate.
Return exactly one JSON object in one of these forms:
{"tool":"search","inputs":{"query":"text","limit":5}}
{"tool":"detail_lookup","inputs":{"inspection_id":1}}
{"tool":"aggregate","inputs":{"group_by":"category"}}
{"final":"short answer for the user"}
Use only those three tools. Do not invent inspection data. If a tool returns an error, explain it or choose a corrected query. After a successful tool response, use its data to answer the user with {"final":"..."}; do not repeat the same successful tool call. Make additional calls only when the request needs distinct information that the first result did not provide."""


class AgentModel(Protocol):
    def next_action(self, messages: list[dict[str, str]]) -> dict[str, Any]: ...


class OllamaModel:
    def __init__(
        self,
        model: str = LOCAL_MODEL,
        base_url: str = OLLAMA_URL,
        timeout_seconds: float = 120.0,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def next_action(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        response = httpx.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "format": "json",
                "stream": False,
                "keep_alive": "5m",
                "options": {"temperature": 0, "num_predict": 160},
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        content = response.json().get("message", {}).get("content", "")
        action = json.loads(content)
        if not isinstance(action, dict):
            raise ValueError("Ollama response must be a JSON object")
        return action


class MockModel:
    """Deterministic model stub; repeat_action can simulate a runaway model."""

    def __init__(
        self,
        actions: list[dict[str, Any]] | None = None,
        *,
        repeat_action: dict[str, Any] | None = None,
    ):
        self.actions = list(actions or [])
        self.repeat_action = repeat_action
        self.calls = 0

    def next_action(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        self.calls += 1
        if self.repeat_action is not None:
            return dict(self.repeat_action)
        if self.actions:
            return self.actions.pop(0)
        return {"final": "I do not have enough information to answer."}


def _append_jsonl(path: str | Path, entry: dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def run_agent(
    user_input: str,
    *,
    model: AgentModel | None = None,
    max_steps: int = DEFAULT_MAX_STEPS,
    tool_executor=execute_tool,
    log_path: str | Path | None = DEFAULT_RUN_LOG,
) -> dict[str, Any]:
    if not isinstance(user_input, str) or not user_input.strip():
        return {
            "answer": "Please enter a question about restaurant inspections.",
            "step_count": 0,
            "tool_call_count": 0,
            "stop_reason": "normal_completion",
            "trace": [],
        }
    if not isinstance(max_steps, int) or isinstance(max_steps, bool) or max_steps < 1:
        raise ValueError("max_steps must be at least 1")


    if is_unsafe_inspection_intent(user_input):
        blocked_text = tool_executor("search", {"query": user_input.strip()})
        try:
            blocked = json.loads(blocked_text)
        except (TypeError, json.JSONDecodeError):
            blocked = {"ok": False, "data": None, "error": "safety rule blocked the request"}
        answer = str(blocked.get("error") or "Request blocked by the inspection safety rule.")
        result_summary = {
            "run_id": str(uuid.uuid4()),
            "user_input": user_input.strip(),
            "answer": answer,
            "step_count": 0,
            "tool_call_count": 1,
            "stop_reason": "safety_block",
            "trace": [{"step": 0, "tool": "search", "input": {"query": user_input.strip()}, "result": blocked, "stop_reason": "safety_block"}],
        }
        if log_path is not None:
            _append_jsonl(log_path, {"timestamp_utc": datetime.now(timezone.utc).isoformat(), **result_summary, "event": "run_finished"})
        return result_summary

    agent_model = model or OllamaModel()
    run_id = str(uuid.uuid4())
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input.strip()},
    ]
    trace = []
    answer = "The agent reached its step limit before producing a final answer."
    stop_reason = "max_steps"
    step_count = 0
    tool_call_count = 0

    while step_count < max_steps:
        step_count += 1
        timestamp = datetime.now(timezone.utc).isoformat()
        try:
            action = agent_model.next_action(messages)
        except Exception as exc:
            stop_reason = "model_error"
            answer = f"The local model request failed: {type(exc).__name__}."
            trace.append(
                {
                    "step": step_count,
                    "tool": None,
                    "input": None,
                    "result": None,
                    "error": type(exc).__name__,
                    "stop_reason": stop_reason,
                }
            )
            if log_path is not None:
                _append_jsonl(log_path, {"run_id": run_id, "timestamp_utc": timestamp, "user_input": user_input.strip(), "step": step_count, "tool": None, "input": None, "result": None, "error": type(exc).__name__, "stop_reason": stop_reason, "event": "step"})
            break

        if isinstance(action, dict) and isinstance(action.get("final"), str):
            answer = action["final"]
            stop_reason = "normal_completion"
            trace.append(
                {
                    "step": step_count,
                    "tool": None,
                    "input": None,
                    "result": None,
                    "assistant_final": answer,
                    "stop_reason": stop_reason,
                }
            )
            if log_path is not None:
                _append_jsonl(log_path, {"run_id": run_id, "timestamp_utc": timestamp, "user_input": user_input.strip(), "step": step_count, "tool": None, "input": None, "result": None, "assistant_final": answer, "stop_reason": stop_reason, "event": "step"})
            break

        tool_name = action.get("tool") if isinstance(action, dict) else None
        tool_inputs = action.get("inputs") if isinstance(action, dict) else None
        if not isinstance(tool_name, str) or not isinstance(tool_inputs, dict):
            stop_reason = "invalid_model_action"
            answer = "The local model returned an invalid tool request."
            trace.append(
                {
                    "step": step_count,
                    "tool": tool_name,
                    "input": tool_inputs,
                    "result": None,
                    "stop_reason": stop_reason,
                }
            )
            if log_path is not None:
                _append_jsonl(log_path, {"run_id": run_id, "timestamp_utc": timestamp, "user_input": user_input.strip(), "step": step_count, "tool": tool_name, "input": tool_inputs, "result": None, "stop_reason": stop_reason, "event": "step"})
            break

        tool_call_count += 1
        result_text = tool_executor(tool_name, tool_inputs)
        try:
            result = json.loads(result_text)
        except (TypeError, json.JSONDecodeError):
            result = {"ok": False, "data": None, "error": "tool returned invalid JSON"}

        safety_block = (
            not result.get("ok", False)
            and "safety rule blocked" in str(result.get("error", "")).lower()
        )
        step = {
            "step": step_count,
            "tool": tool_name,
            "input": tool_inputs,
            "result": result,
            "stop_reason": "safety_block" if safety_block else None,
        }
        trace.append(step)
        if log_path is not None:
            _append_jsonl(
                log_path,
                {
                    "run_id": run_id,
                    "timestamp_utc": timestamp,
                    "user_input": user_input.strip(),
                    **step,
                    "event": "step",
                },
            )

        if safety_block:
            stop_reason = "safety_block"
            answer = str(result.get("error"))
            break

        messages.append(
            {
                "role": "assistant",
                "content": json.dumps({"tool": tool_name, "inputs": tool_inputs}),
            }
        )
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Tool result for {tool_name}: {json.dumps(result, ensure_ascii=False)}\n"
                    "Use this result to answer the user's request now. If it succeeded, return a final JSON object; do not repeat this call."
                ),
            }
        )
        if step_count >= max_steps:
            stop_reason = "max_steps"
            answer = "The agent stopped because it reached the configured max_steps limit."
            break

    result_summary = {
        "run_id": run_id,
        "user_input": user_input.strip(),
        "answer": answer,
        "step_count": step_count,
        "tool_call_count": tool_call_count,
        "stop_reason": stop_reason,
        "trace": trace,
    }
    if log_path is not None:
        _append_jsonl(
            log_path,
            {
                "run_id": run_id,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                **{key: result_summary[key] for key in ("user_input", "answer", "step_count", "tool_call_count", "stop_reason")},
                "event": "run_finished",
            },
        )
    return result_summary
