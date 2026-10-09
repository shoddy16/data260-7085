from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.database import Base, engine
from models.models import Inspection, InspectionRelated, Restaurant, User, Session
from routers.auth import router as auth_router
from routers.inspections import router as inspections_router
from routers.n_plus_one import router as n_plus_one_router
from routers.restaurants import router as restaurants_router
from routers.hw6 import router as hw6_router


Base.metadata.create_all(bind=engine)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(inspections_router)
app.include_router(restaurants_router)
app.include_router(n_plus_one_router)
app.include_router(hw6_router)
