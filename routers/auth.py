from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import Session

from database.database import get_db
from jwt_auth import authenticate_user, create_access_token, get_current_user

router = APIRouter()


@router.post("/login")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate_user(db, username, password)
    if user is None:
        raise HTTPException(
            status_code=401, detail="Invalid username or password", headers={"WWW-Authenticate": "Bearer"}
        )
    return {"access_token": create_access_token(user.username, user.role), "token_type": "bearer"}


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    return {"message": "JWT logout is client-side; discard the bearer token."}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "role": user.role}
