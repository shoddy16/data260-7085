import os

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from routers.auth import router as auth_router


app = FastAPI()

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-key")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    https_only=True,
    same_site="lax",
    max_age=3600
)

app.include_router(auth_router)
