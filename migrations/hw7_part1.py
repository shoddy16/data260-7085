"""Idempotent HW7 MySQL user/role migration."""

from sqlalchemy import inspect, text

from database.database import engine


def migrate() -> None:
    if engine.dialect.name != "mysql":
        raise RuntimeError("HW7 authentication migration targets MySQL; no schema changes made")
    inspector = inspect(engine)
    columns = {item["name"] for item in inspector.get_columns("users")}
    with engine.begin() as connection:
        if "username" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(255) NULL"))
            connection.execute(text("UPDATE users SET username = email WHERE username IS NULL"))
            connection.execute(text("ALTER TABLE users MODIFY username VARCHAR(255) NOT NULL"))
            connection.execute(text("CREATE UNIQUE INDEX uq_users_username ON users (username)"))
        if "role" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'reader'"))


if __name__ == "__main__":
    migrate()
    from hw7_seed import seed_users

    print(f"created_users={seed_users()}")
