import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .models import Base
from dotenv import load_dotenv
load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def init_db():
    """Initializes tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Provides a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()