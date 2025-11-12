from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.auth import get_current_user, get_password_hash
from app.db.database import engine
from app.models import User
from app.schemas import UserOut, ProfileUpdate

router = APIRouter()

@router.get("/me", response_model=UserOut)
def read_profile(user=Depends(get_current_user)):
    return user

@router.put("/me", response_model=UserOut)
def update_profile(data: ProfileUpdate, user=Depends(get_current_user)):
    with Session(engine) as session:
        db_user = session.get(User, user.id)
        if data.full_name is not None:
            db_user.full_name = data.full_name
        if data.email is not None:
            db_user.email = data.email
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

@router.delete("/me", status_code=204)
def delete_account(user=Depends(get_current_user)):
    with Session(engine) as session:
        db_user = session.get(User, user.id)
        session.delete(db_user)
        session.commit()
        return None
