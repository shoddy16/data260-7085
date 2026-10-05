import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:password@localhost/db_session_basede26"
)

engine_options = {"pool_pre_ping": True}
if DATABASE_URL in {"sqlite://", "sqlite:///:memory:"}:
    engine_options.update(
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
elif DATABASE_URL.startswith("mysql+"):
    engine_options["connect_args"] = {
        "connect_timeout": 3,
        "read_timeout": 5,
        "write_timeout": 5,
    }
engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
