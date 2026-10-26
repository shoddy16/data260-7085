"""Pure-Python sandbox file tools and an independently testable safety gate."""

from __future__ import annotations

import difflib
import glob
import re
import subprocess
from pathlib import Path

SAFE_PREFIXES = ("python ", "python.exe ", "py ", "dir", "type ", "Get-ChildItem", "Select-String", "rg ")
DESTRUCTIVE_PATTERNS = (
    r"\brm\s+-rf\b",
    r"\bdel\s+/[sqf]+\b",
    r"\bformat\b",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r"\bsudo\b",
    r"\bchmod\b",
    r"\bchown\b",
    r"\bnet\s+user\b",
    r">\s*/(?:etc|root|dev)\b",
)


def _inside(path: str | Path, sandbox: Path) -> Path:
    candidate = Path(path).resolve()
    root = sandbox.resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("path is outside the temporary course sandbox")
    return candidate


def read_file(path: str | Path, sandbox: Path, max_lines: int | None = None) -> str:
    text = _inside(path, sandbox).read_text(encoding="utf-8")
    return "\n".join(text.splitlines()[:max_lines]) if max_lines else text


def write_file(path: str | Path, content: str, sandbox: Path) -> str:
    target = _inside(path, sandbox)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return str(target)


def edit_file(path: str | Path, old: str, new: str, sandbox: Path) -> str:
    target = _inside(path, sandbox)
    before = target.read_text(encoding="utf-8")
    after = before.replace(old, new, 1)
    if before == after:
        raise ValueError("edit target was not found")
    target.write_text(after, encoding="utf-8")
    return "\n".join(difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm=""))


def glob_files(pattern: str, sandbox: Path) -> list[str]:
    return [
        str(Path(item).resolve()) for item in glob.glob(str(sandbox / pattern), recursive=True) if Path(item).is_file()
    ]


def search_in_files(query: str, sandbox: Path, file_pattern: str = "**/*") -> list[dict[str, object]]:
    matches = []
    for path in glob_files(file_pattern, sandbox):
        try:
            for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
                if query in line:
                    matches.append({"path": path, "line": line_number, "text": line})
        except UnicodeDecodeError:
            continue
    return matches


def is_destructive(command: str) -> bool:
    return any(re.search(pattern, command, re.I) for pattern in DESTRUCTIVE_PATTERNS)


def confirm_bash(command: str, auto_approve: bool = False) -> dict[str, object]:
    if is_destructive(command):
        return {"allowed": bool(auto_approve), "reason": "destructive command requires explicit confirmation"}
    if not any(command.strip().lower().startswith(prefix.lower()) for prefix in SAFE_PREFIXES):
        return {"allowed": False, "reason": "command is not in SAFE_PREFIXES"}
    return {"allowed": True, "reason": "command matches SAFE_PREFIXES"}


def bash(command: str, sandbox: Path, auto_approve: bool = False) -> dict[str, object]:
    decision = confirm_bash(command, auto_approve)
    if not decision["allowed"]:
        return decision
    result = subprocess.run(command, cwd=sandbox, shell=True, capture_output=True, text=True, timeout=10)
    return {
        "allowed": True,
        "reason": decision["reason"],
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
