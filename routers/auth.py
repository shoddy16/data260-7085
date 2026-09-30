from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database.database import get_db
from auth import (
    login_user,
    logout_user,
    get_current_user,
    SESSION_TIMEOUT
)

router = APIRouter()


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    token = login_user(db, request, username, password)

    if not token:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid username or password"}
        )

    response = JSONResponse(
        content={
            "message": "Login successful",
            "username": username
        }
    )

    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_TIMEOUT
    )

    return response


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("session")

    if token:
        logout_user(db, token)

    response = JSONResponse(
        content={"message": "Logged out successfully"}
    )

    response.delete_cookie("session")

    return response


@router.get("/session")
def session(
    request: Request,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("session")
    user = get_current_user(db, token)

    if not user:
        return JSONResponse(
            status_code=401,
            content={"authenticated": False}
        )

    return {
        "authenticated": True,
        "username": user.email
    }