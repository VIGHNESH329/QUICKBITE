import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Ensure target directory exists for SQLite if a file path is specified
if "sqlite:///" in settings.DATABASE_URL:
    db_file_path = settings.DATABASE_URL.replace("sqlite:///", "")
    # Handle absolute Linux/Windows paths
    if db_file_path.startswith("/"):
        db_dir = os.path.dirname(db_file_path)
    else:
        db_dir = os.path.dirname(os.path.abspath(db_file_path))
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except OSError:
            pass

# SQLite connection with thread check disabled for multithreaded FastAPI worker
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency that yields a database session and ensures it is closed after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
