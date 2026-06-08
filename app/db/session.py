from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session 
from app.core.config import settings

engine = create_engine(
    settings.database_url,
    echo = False,
    pool_pre_ping = True,
    pool_size =10,
    max_overflow=20,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_= Session,
    expire_on_commit = False,
)

def get_db_session() -> Session:

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

        