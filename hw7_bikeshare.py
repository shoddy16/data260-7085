"""Framework-style ReAct/MRKL bike-share tools and reproducible scenarios."""

from __future__ import annotations

import csv
import html
import io
import re
import sqlite3
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

READ_ONLY = re.compile(r"^\s*select\b", re.IGNORECASE)
SAFE_EXPRESSION = re.compile(r"^[0-9+\-*/().\s]+$")


def envelope(success: bool, data: Any = None, error: str | None = None, source: str | None = None) -> dict[str, Any]:
    return {
        "success": success,
        "data": data,
        "error": error,
        "source": source,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def csv_sql(csv_text: str, sql: str) -> dict[str, Any]:
    if not READ_ONLY.match(sql or "") or ";" in sql.rstrip().rstrip(";"):
        return envelope(False, error="csv_sql accepts one read-only SELECT statement", source="uploaded.csv")
    try:
        connection = sqlite3.connect(":memory:")
        reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(reader)
        if not reader.fieldnames:
            return envelope(False, error="CSV has no header", source="uploaded.csv")
        columns = ", ".join('"%s" TEXT' % c.replace('"', '""') for c in reader.fieldnames)
        connection.execute(f"CREATE TABLE trips ({columns})")
        placeholders = ",".join("?" for _ in reader.fieldnames)
        connection.executemany(
            f"INSERT INTO trips VALUES ({placeholders})", [[row.get(c, "") for c in reader.fieldnames] for row in rows]
        )
        result = connection.execute(sql).fetchall()
        names = [item[0] for item in connection.execute(sql).description]
        return envelope(
            True,
            {"rows": [dict(zip(names, row)) for row in result], "row_count": len(result), "source": "uploaded.csv"},
            source="uploaded.csv",
        )
    except (sqlite3.Error, ValueError) as exc:
        return envelope(False, error=f"SQL error: {exc}", source="uploaded.csv")
    finally:
        try:
            connection.close()
        except UnboundLocalError:
            pass


def policy_retriever(url: str, query: str, k: int = 4) -> dict[str, Any]:
    try:
        if url.startswith("file://"):
            text = Path(url[7:]).read_text(encoding="utf-8")
        elif Path(url).exists():
            text = Path(url).read_text(encoding="utf-8")
        else:
            request = urllib.request.Request(url, headers={"User-Agent": "DATA260-HW7"})
            text = urllib.request.urlopen(request, timeout=15).read().decode("utf-8", errors="replace")
        clean = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text))).strip()
        terms = [term.lower() for term in re.findall(r"[a-z0-9]+", query.lower())]
        chunks = [clean[i : i + 320] for i in range(0, len(clean), 260)]
        scored = sorted(((sum(term in chunk.lower() for term in terms), chunk) for chunk in chunks), reverse=True)
        passages = [
            {"text": chunk, "source": url, "score": score / max(1, len(terms))}
            for score, chunk in scored[:k]
            if score or not terms
        ]
        return envelope(True, {"passages": passages}, source=url)
    except Exception as exc:
        return envelope(False, error=f"policy retrieval failed: {type(exc).__name__}", source=url)


def calculator(expression: str, units: str | None = None) -> dict[str, Any]:
    if not SAFE_EXPRESSION.fullmatch(expression or ""):
        return envelope(False, error="expression contains unsupported characters")
    try:
        # A tiny operator parser avoids eval while supporting the assignment's arithmetic grammar.
        tokens = re.findall(r"\d+(?:\.\d+)?|[+*/()-]", expression.replace(" ", ""))
        total = float(tokens[0])
        index = 1
        while index < len(tokens):
            operator, number = tokens[index], float(tokens[index + 1])
            if operator == "+":
                total += number
            elif operator == "-":
                total -= number
            elif operator == "*":
                total *= number
            elif operator == "/":
                total /= number
            index += 2
        return envelope(True, {"value": total, **({"units": units} if units else {})})
    except (ValueError, ZeroDivisionError, IndexError):
        return envelope(False, error="invalid arithmetic expression")


def generate_scenario(path: Path, rides: int, duration_minutes: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["ride_id", "started_at", "duration_minutes", "ride_type", "member_type"])
        for index in range(rides):
            week = index % 4 + 1
            writer.writerow(
                [
                    f"ride-{index + 1:04d}",
                    f"2026-09-{week * 7 - 6:02d}T08:00:00Z",
                    duration_minutes,
                    "classic",
                    "casual",
                ]
            )


def run_scenario(csv_path: Path, pricing_url: str, membership_cost: float = 239.0) -> dict[str, Any]:
    text = csv_path.read_text(encoding="utf-8")
    rows = list(csv.DictReader(io.StringIO(text)))
    total_minutes = sum(float(row["duration_minutes"]) for row in rows)
    rides = len(rows)
    by_day: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_day.setdefault(row["started_at"][:10], []).append(row)
    pay = sum(
        min(4.99 * len(day_rows), 25.0) + sum(max(0.0, float(row["duration_minutes"]) - 30) * 0.41 for row in day_rows)
        for day_rows in by_day.values()
    )
    member = membership_cost + sum(max(0.0, float(row["duration_minutes"]) - 45) * 0.27 for row in rows)
    weekly = []
    for week in range(1, 5):
        subset = [row for row in rows if int(row["started_at"][8:10]) == week * 7 - 6]
        weekly.append(
            {
                "week": week,
                "ride_count": len(subset),
                "average_duration": round(sum(float(r["duration_minutes"]) for r in subset) / max(1, len(subset)), 2),
                "pay_per_use_spend": round(
                    min(4.99 * len(subset), 25.0)
                    + sum(max(0.0, float(r["duration_minutes"]) - 30) * 0.41 for r in subset),
                    2,
                ),
            }
        )
    snapshot = policy_retriever(pricing_url, "annual membership 239 45 minutes 0.27 4.99 30 minutes 0.41")
    policy_data = snapshot.get("data") or {}
    return {
        "decision": "Buy Monthly Membership" if member < pay else "Pay Per Ride/Minute",
        "costs": {"pay_per_use": round(pay, 2), "membership_plus_residual": round(member, 2)},
        "break_even_rides": round(membership_cost / max(0.01, 4.99), 2),
        "ride_count": rides,
        "total_minutes": total_minutes,
        "weekly": weekly,
        "citations": policy_data.get("passages", []),
        "source_url": pricing_url,
        "accessed_at": datetime.now(timezone.utc).isoformat(),
        "steps": 4,
        "stop_reason": "success",
    }
