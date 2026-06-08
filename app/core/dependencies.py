from sqlalchemy.orm import Session 
from fastapi import Depends
from app.db.session import get_db_session

def get_db(session: Session = Depends(get_db_session)) -> Session:

    return session

    