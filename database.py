import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# Define constants for connection details
db_host = os.environ.get("MYSQL_HOST", "localhost")
db_user = os.environ.get("MYSQL_USER", "root")
db_pass = os.environ.get("MYSQL_PASSWORD", "your_password")
db_name = os.environ.get("MYSQL_DB", "preferences_db")
db_port = os.environ.get("MYSQL_PORT", "3306")

# SQLAlchemy Connection String Format:
# mysql+pymysql://user:password@host:port/db_name

engine_args = {
    "pool_pre_ping": True,
    "pool_recycle": 3600,
    "pool_size": 5,
    "max_overflow": 10
}

if os.environ.get("DATABASE_URL"):
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if "sqlite" in DATABASE_URL:
        # SQLite doesn't support pool_size/max_overflow with default pool
        # and checking same thread is needed for FastAPI
        engine_args = {
            "connect_args": {"check_same_thread": False},
            "poolclass": None  # Use default pool logic for sqlite
        }
else:
    DATABASE_URL = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

# create the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    **engine_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
