"""The single safe tool entry point used by offline tests and the agent."""

import json
import re
from typing import Any

from domain.inspection_tools import (
    InspectionTools,
    default_inspection_tools,
    failure,
)


_UNSAFE_INSPECTION_INTENT = re.compile(
    r"\b(?:evade|bypass|falsify|fake|conceal|hide)\b.{0,60}\b(?:inspection|inspector|violation|score|report)s?\b"
    r"|\b(?:inspection|inspector|violation|score|report)s?\b.{0,60}\b(?:evade|bypass|falsify|fake|conceal|hide)\b",
    re.IGNORECASE,
)


def _is_safety_blocked(name: str, inputs: dict[str, Any]) -> bool:
    if name != "search":
        return False
    query = inputs.get("query")
    return isinstance(query, str) and bool(_UNSAFE_INSPECTION_INTENT.search(query))


def is_unsafe_inspection_intent(query: str) -> bool:
    return isinstance(query, str) and bool(_UNSAFE_INSPECTION_INTENT.search(query))


def execute_tool(
    name: str,
    inputs: dict[str, Any],
    *,
    tools: InspectionTools | None = None,
) -> str:
    """Dispatch one of the three read-only domain tools and return JSON text."""
    if not isinstance(name, str) or not name:
        return json.dumps(failure("tool name must be a non-empty string"))
    if not isinstance(inputs, dict):
        return json.dumps(failure("inputs must be a JSON object"))
    if _is_safety_blocked(name, inputs):
        envelope = failure(
            "safety rule blocked requests to evade or falsify restaurant inspections"
        )
        return json.dumps(envelope)

    domain_tools = tools or default_inspection_tools
    handlers = {
        "search": lambda: domain_tools.search(
            inputs.get("query"), inputs.get("limit", 5)
        ),
        "detail_lookup": lambda: domain_tools.detail_lookup(
            int(inputs["inspection_id"])
            if isinstance(inputs.get("inspection_id"), str)
            and inputs["inspection_id"].isdigit()
            else inputs.get("inspection_id")
        ),
        "aggregate": lambda: domain_tools.aggregate(inputs.get("group_by", "category")),
    }
    handler = handlers.get(name)
    if handler is None:
        envelope = failure("unknown tool name")
    else:
        try:
            envelope = handler()
        except Exception:
            envelope = failure("tool execution failed")
    return json.dumps(envelope, ensure_ascii=False, separators=(",", ":"))
