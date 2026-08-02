# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Default SQLite database for instant out-of-the-box execution
DATABASE_URL = "sqlite:///./traffic.db"

# Uncomment for PostgreSQL production setup:
# DATABASE_URL = "postgresql://postgres:KEERTHI@localhost:5432/traffic_management"

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()