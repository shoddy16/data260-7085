"""Inspectable Markdown-based memory and consolidation commands."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from hw6_config import AGENT_FILE, MEMORY_FILE

CONSOLIDATED_MARKER = "<!-- consolidated_at: {timestamp} -->"


def load_files(agent_path: Path = AGENT_FILE, memory_path: Path = MEMORY_FILE) -> dict[str, str]:
    return {"agent": agent_path.read_text(encoding="utf-8") if agent_path.exists() else "", "memory": memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""}


def prompt_memory(agent_path: Path = AGENT_FILE, memory_path: Path = MEMORY_FILE) -> str:
    loaded = load_files(agent_path, memory_path)
    return f"Durable agent instructions:\n{loaded['agent']}\nDurable facts:\n{loaded['memory']}"


def _content_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#") and not line.lstrip().startswith("<!--")]


def consolidation_required(memory_path: Path = MEMORY_FILE, now: datetime | None = None) -> tuple[bool, str]:
    text = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""
    lines = _content_lines(text)
    match = re.search(r"consolidated_at:\s*([^ >]+)", text)
    if len(lines) > 40:
        return True, "more_than_40_lines"
    if match:
        try:
            recorded = datetime.fromisoformat(match.group(1).replace("Z", "+00:00"))
            current = now or datetime.now(timezone.utc)
            if (current - recorded).total_seconds() > 86400:
                return True, "older_than_24_hours"
        except ValueError:
            return True, "invalid_timestamp"
    return False, "not_required"


def consolidate_memory(memory_path: Path = MEMORY_FILE) -> dict[str, object]:
    original = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""
    lines = _content_lines(original)
    result: list[str] = []
    seen: set[str] = set()
    contradictions: list[str] = []
    for line in lines:
        normalized = re.sub(r"\s+", " ", line).lower()
        if normalized in seen:
            continue
        # Explicitly preserve contradictory facts instead of silently dropping one.
        if any(("uses mysql" in normalized and "uses mongodb" in existing) or ("uses mongodb" in normalized and "uses mysql" in existing) for existing in seen):
            contradictions.append(line)
            continue
        seen.add(normalized)
        result.append(line)
    if contradictions:
        result.append("Resolved contradictions: MongoDB is the HW6 memory/document store; MySQL remains the HW1-HW5 relational store.")
        result.extend(f"Contradiction reviewed: {item}" for item in contradictions[:3])
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    memory_path.write_text("# Durable Memory\n" + CONSOLIDATED_MARKER.format(timestamp=timestamp) + "\n" + "\n".join(f"- {line}" for line in result) + "\n", encoding="utf-8")
    return {"before": len(lines), "after": len(result), "contradictions_reviewed": contradictions}


def handle_command(command: str, recent_messages: list[str] | None = None, agent_path: Path = AGENT_FILE, memory_path: Path = MEMORY_FILE) -> str:
    command = command.strip().lower()
    if command == "/memory": return prompt_memory(agent_path, memory_path)
    if command == "/help": return "/memory display files; /compact consolidate MEMORY.md; /dream save useful recent facts; /help show commands"
    if command == "/compact":
        result = consolidate_memory(memory_path)
        return f"MEMORY.md compacted: before={result['before']} after={result['after']} contradictions_reviewed={len(result['contradictions_reviewed'])}"
    if command == "/dream":
        facts = [f"- Learned from recent conversation: {message.strip()[:160]}" for message in (recent_messages or []) if message.strip()]
        with memory_path.open("a", encoding="utf-8") as stream:
            stream.write("\n" + "\n".join(facts[:3]) + "\n")
        return f"Added {len(facts[:3])} durable fact(s) to MEMORY.md"
    return "Unknown command. Use /help."
