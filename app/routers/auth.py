from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import timedelta

from app.schemas import UserCreate, Token, UserOut
from app.db.database import engine
from app.models import User
from app.auth import get_password_hash, verify_password, create_access_token, get_user_by_email

router = APIRouter()

@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate):
    with Session(engine) as session:
        # simple check
        if session.exec(select(User).where(User.email == user_in.email)).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        user = User(email=user_in.email, hashed_password=get_password_hash(user_in.password), full_name=user_in.full_name)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        statement = select(User).where(User.email == form_data.username)
        user = session.exec(statement).first()
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        access_token_expires = timedelta(minutes=60*24)
        token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
        return {"access_token": token, "token_type": "bearer"}

@router.post("/logout", status_code=204)
def logout():
    return None
