"""Create deterministic HW7 demo users in the configured database."""

from database.database import SessionLocal
from jwt_auth import hash_password
from models.models import User

DEMO_USERS = (
    ("reader", "reader", "reader"),
    ("writer", "writer", "writer"),
    ("moderator", "moderator", "moderator"),
)


def seed_users(db=None) -> int:
    owns_session = db is None
    db = db or SessionLocal()
    created = 0
    try:
        for username, password, role in DEMO_USERS:
            user = db.query(User).filter(User.username == username).first()
            if user is None:
                db.add(
                    User(
                        username=username,
                        name=username.title(),
                        email=f"{username}@hw7.local",
                        password_hash=hash_password(password),
                        role=role,
                    )
                )
                created += 1
        db.commit()
        return created
    finally:
        if owns_session:
            db.close()


if __name__ == "__main__":
    print(f"created={seed_users()}")
