import secrets
from datetime import datetime, timedelta

from fastapi import Request
from sqlalchemy.orm import Session

from models.models import User, Session as SessionModel

SESSION_TIMEOUT = 1000


USERS = {
    "admin": "data260"
}


def login_user(
    db: Session,
    request: Request,
    username: str,
    password: str
):
    if username not in USERS or USERS[username] != password:
        return None

    user = db.query(User).filter(User.email == username).first()

    if not user:
        user = User(
            name=username,
            email=username,
            password_hash=password
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = secrets.token_urlsafe(32)

    session = SessionModel(
        id=token,
        user_id=user.id,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(seconds=SESSION_TIMEOUT)
    )

    db.add(session)
    db.commit()

    return token


def logout_user(db: Session, token: str):
    session = db.query(SessionModel).filter(
        SessionModel.id == token
    ).first()

    if session:
        db.delete(session)
        db.commit()


def get_current_user(db: Session, token: str):
    if not token:
        return None

    session = db.query(SessionModel).filter(
        SessionModel.id == token
    ).first()

    if not session:
        return None

    if session.expires_at < datetime.utcnow():
        db.delete(session)
        db.commit()
        return None

    user = db.query(User).filter(
        User.id == session.user_id
    ).first()

    return user