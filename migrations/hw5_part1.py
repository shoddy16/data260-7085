"""Idempotent MySQL migration for the HW5 restaurant/inspection relationship.

Run once from the repository root before starting the updated API against an
existing HW4 database:
    python -m migrations.hw5_part1

The script adds columns and backfills them; it does not drop or rewrite the
existing HW1-HW4 inspection fields.
"""

from uuid import uuid4

from sqlalchemy import inspect, text

from database.database import engine
from models.models import Restaurant


def _columns(connection, table_name):
    return {column["name"] for column in inspect(connection).get_columns(table_name)}


def _indexes(connection, table_name):
    return {item["name"] for item in inspect(connection).get_indexes(table_name)}


def migrate():
    if engine.dialect.name != "mysql":
        raise RuntimeError(
            "This migration targets the configured MySQL database; "
            "no schema changes were made."
        )

    Restaurant.__table__.create(bind=engine, checkfirst=True)

    with engine.begin() as connection:
        columns = _columns(connection, "inspections")
        additions = {
            "restaurant_id": "INTEGER NULL",
            "inspection_code": "VARCHAR(64) NULL",
            "score": "INTEGER NOT NULL DEFAULT 100",
            "created_at": "DATETIME NULL",
            "updated_at": "DATETIME NULL",
        }
        for column_name, definition in additions.items():
            if column_name not in columns:
                connection.execute(
                    text(f"ALTER TABLE inspections ADD COLUMN {column_name} {definition}")
                )

        # Recheck columns after DDL, then reuse one Restaurant row for each
        # distinct name/location pair represented by legacy inspection data.
        rows = connection.execute(
            text(
                "SELECT id, restaurantName, location, restaurant_id "
                "FROM inspections ORDER BY id"
            )
        ).mappings().all()
        restaurant_ids = {}
        for row in rows:
            if row["restaurant_id"] is not None:
                continue
            key = (row["restaurantName"], row["location"])
            if key not in restaurant_ids:
                existing = connection.execute(
                    text(
                        "SELECT id FROM restaurants "
                        "WHERE name = :name AND location = :location LIMIT 1"
                    ),
                    {"name": key[0], "location": key[1]},
                ).first()
                if existing:
                    restaurant_ids[key] = existing[0]
                else:
                    code = f"s7085-r-{uuid4().hex[:8]}"
                    result = connection.execute(
                        text(
                            "INSERT INTO restaurants (name, location, code, created_at, updated_at) "
                            "VALUES (:name, :location, :code, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                        ),
                        {"name": key[0], "location": key[1], "code": code},
                    )
                    restaurant_ids[key] = result.lastrowid
            connection.execute(
                text("UPDATE inspections SET restaurant_id = :restaurant_id WHERE id = :id"),
                {"restaurant_id": restaurant_ids[key], "id": row["id"]},
            )

        connection.execute(
            text(
                "UPDATE inspections SET inspection_code = CONCAT('s7085-i-', LPAD(id, 8, '0')) "
                "WHERE inspection_code IS NULL OR inspection_code = ''"
            )
        )
        connection.execute(
            text(
                "UPDATE inspections SET created_at = CURRENT_TIMESTAMP "
                "WHERE created_at IS NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE inspections SET updated_at = CURRENT_TIMESTAMP "
                "WHERE updated_at IS NULL"
            )
        )

        fk_names = {
            fk["name"]
            for fk in inspect(connection).get_foreign_keys("inspections")
        }
        if "fk_inspections_restaurant_id" not in fk_names:
            connection.execute(
                text(
                    "ALTER TABLE inspections ADD CONSTRAINT fk_inspections_restaurant_id "
                    "FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE RESTRICT"
                )
            )
        connection.execute(text("ALTER TABLE inspections MODIFY restaurant_id INTEGER NOT NULL"))

        indexes = _indexes(connection, "inspections")
        if "ix_inspections_restaurant_id" not in indexes:
            connection.execute(
                text("CREATE INDEX ix_inspections_restaurant_id ON inspections (restaurant_id)")
            )
        if "uq_inspections_code" not in indexes:
            connection.execute(
                text("CREATE UNIQUE INDEX uq_inspections_code ON inspections (inspection_code)")
            )

    print("HW5 Part 1 migration completed. Existing inspection fields were preserved.")


if __name__ == "__main__":
    migrate()
