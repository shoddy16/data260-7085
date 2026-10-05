from typing import Any, Protocol

import re

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from database.database import SessionLocal
from models.models import Inspection, Restaurant
from reliability import retry_sync


def success(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data, "error": None}


def failure(message: str) -> dict[str, Any]:
    return {"ok": False, "data": None, "error": message}


class InspectionRepository(Protocol):
    def search(self, query: str, limit: int) -> list[dict[str, Any]]: ...

    def detail(self, inspection_id: int) -> dict[str, Any] | None: ...

    def aggregate(self, group_by: str) -> list[dict[str, Any]]: ...


def _record(inspection: Inspection, restaurant: Restaurant) -> dict[str, Any]:
    return {
        "id": inspection.id,
        "inspection_code": inspection.inspection_code,
        "restaurant_id": restaurant.id,
        "restaurant": restaurant.name,
        "location": restaurant.location,
        "category": inspection.category,
        "description": inspection.description,
        "score": inspection.score,
        "created_at": inspection.created_at.isoformat() if inspection.created_at else None,
    }


class SQLInspectionRepository:
    """Read-only view over the same SQLAlchemy database used by FastAPI."""

    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    def _read(self, operation):
        return retry_sync(operation, max_attempts=3)

    def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        stop_words = {
            "a", "an", "and", "at", "find", "for", "from", "in", "inspection",
            "inspections", "me", "of", "please", "record", "records", "restaurant",
            "restaurants", "search", "show", "the", "what", "where", "which",
        }
        tokens = [
            token for token in re.findall(r"[a-z0-9]+", query.lower())
            if token not in stop_words
        ]

        def operation():
            with self.session_factory() as db:
                term = f"%{query}%"
                search_columns = (
                    Restaurant.name,
                    Restaurant.location,
                    Inspection.category,
                    Inspection.description,
                    Inspection.inspection_code,
                )
                filters = [
                    or_(*(column.ilike(f"%{token}%") for column in search_columns))
                    for token in tokens
                ]
                text_filter = or_(
                    *(column.ilike(term) for column in search_columns),
                    and_(*filters) if filters else False,
                )
                candidates = (
                    db.query(Inspection, Restaurant)
                    .join(Restaurant, Inspection.restaurant_id == Restaurant.id)
                    .filter(text_filter)
                    .order_by(Inspection.id)
                    .limit(max(limit * 20, 100))
                    .all()
                )
                # SQL LIKE treats a numeric token such as "1" as a substring,
                # which also matches 11, 19, etc. Apply whole-token matching
                # across the joined text fields before enforcing the result cap.
                rows = []
                for inspection, restaurant in candidates:
                    searchable = " ".join(
                        str(value or "")
                        for value in (
                            restaurant.name,
                            restaurant.location,
                            inspection.category,
                            inspection.description,
                            inspection.inspection_code,
                        )
                    ).lower()
                    if all(
                        re.search(rf"\b{re.escape(token)}\b", searchable)
                        for token in tokens
                    ):
                        rows.append((inspection, restaurant))
                    if len(rows) >= limit:
                        break
                return [_record(inspection, restaurant) for inspection, restaurant in rows]

        return self._read(operation)

    def detail(self, inspection_id: int) -> dict[str, Any] | None:
        def operation():
            with self.session_factory() as db:
                row = (
                    db.query(Inspection, Restaurant)
                    .join(Restaurant, Inspection.restaurant_id == Restaurant.id)
                    .filter(Inspection.id == inspection_id)
                    .first()
                )
                if row is None:
                    return None
                return _record(*row)

        return self._read(operation)

    def aggregate(self, group_by: str) -> list[dict[str, Any]]:
        def operation():
            with self.session_factory() as db:
                if group_by == "category":
                    group_column = Inspection.category
                    query = db.query(
                        group_column.label("group"),
                        func.count(Inspection.id).label("inspection_count"),
                        func.avg(Inspection.score).label("average_score"),
                    ).group_by(group_column)
                else:
                    group_column = Restaurant.name
                    query = (
                        db.query(
                            group_column.label("group"),
                            func.count(Inspection.id).label("inspection_count"),
                            func.avg(Inspection.score).label("average_score"),
                        )
                        .join(Restaurant, Inspection.restaurant_id == Restaurant.id)
                        .group_by(group_column)
                    )
                return [
                    {
                        "group": row.group,
                        "inspection_count": row.inspection_count,
                        "average_score": round(float(row.average_score), 2),
                    }
                    for row in query.order_by(group_column).all()
                ]

        return self._read(operation)


class InspectionTools:
    """Validate domain-tool inputs and keep every result in one envelope."""

    def __init__(self, repository: InspectionRepository):
        self.repository = repository

    def search(self, query: str, limit: int = 5) -> dict[str, Any]:
        if not isinstance(query, str) or not query.strip():
            return failure("query must be a non-empty string")
        if not isinstance(limit, int) or not 1 <= limit <= 25:
            return failure("limit must be between 1 and 25")
        try:
            return success(self.repository.search(query.strip(), limit))
        except Exception:
            return failure("inspection search failed; verify the HW5 database migration has been applied")

    def detail_lookup(self, inspection_id: int) -> dict[str, Any]:
        if not isinstance(inspection_id, int) or inspection_id <= 0:
            return failure("inspection_id must be a positive integer")
        try:
            result = self.repository.detail(inspection_id)
            if result is None:
                return failure("inspection not found")
            return success(result)
        except Exception:
            return failure("inspection lookup failed; verify the HW5 database migration has been applied")

    def aggregate(self, group_by: str = "category") -> dict[str, Any]:
        if group_by not in {"category", "restaurant"}:
            return failure("group_by must be 'category' or 'restaurant'")
        try:
            return success(self.repository.aggregate(group_by))
        except Exception:
            return failure("inspection aggregation failed; verify the HW5 database migration has been applied")


default_inspection_tools = InspectionTools(SQLInspectionRepository())
