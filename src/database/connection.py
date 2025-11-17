from sqlmodel import create_engine, Session, SQLModel
from typing import Generator
from src.config import DATABASE_URL, ENV

if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set in environment variables")

# Create engine
# connect_args is only necessary for SQLite
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(
    DATABASE_URL,
    echo=ENV == "development",
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args=connect_args
)

def create_db_and_tables():
    """Create all tables defined in SQLModel models"""
    SQLModel.metadata.create_all(engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get a database session.
    Use this function with Depends() in FastAPI endpoints.
    """
    with Session(engine) as session:
        yield session
