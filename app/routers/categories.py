from typing import List
from fastapi import APIRouter
from sqlmodel import select, Session
from app.db.database import engine
from app.models import Category
from app.schemas import CategoryOut

router = APIRouter()

@router.get("/", response_model=List[CategoryOut])
def list_categories():
    with Session(engine) as session:
        statement = select(Category)
        return session.exec(statement).all()
