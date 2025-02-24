import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

# Load the .env file from the project root
project_root = os.path.join(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(dotenv_path=os.path.join(project_root, ".env"))

# Build the database URL from environment variables.
# Example environment variables:
#   DB_ENGINE (e.g., "sqlite" or "postgresql")
#   For SQLite, use DB_DATA_PATH (default: "../data/test.db")
#   For other databases, use DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, and DB_NAME

DB_ENGINE = os.getenv("DB_ENGINE", "sqlite")

if DB_ENGINE == "sqlite":
    DB_DATA_PATH = os.getenv("DB_DATA_PATH", "../data/test.db")
    DATABASE_URL = f"sqlite:///{DB_DATA_PATH}"
else:
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")
    DATABASE_URL = f"{DB_ENGINE}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to provide a database session
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()