
from sqlmodel import Session, select
from app.db.database import engine, init_db
from app.models import User
from app.auth import get_password_hash
import os


def create_test_user(email: str, password: str, full_name: str = "Test User"):
    init_db()
    with Session(engine) as session:
        stmt = select(User).where(User.email == email)
        existing = session.exec(stmt).first()
        if existing:
            print(f"User already exists: {email}")
            return existing
        hashed = get_password_hash(password)
        user = User(email=email, hashed_password=hashed, full_name=full_name)
        session.add(user)
        session.commit()
        session.refresh(user)
        print(f"Created user {email} (id={user.id})")
        return user


if __name__ == "__main__":
    email = os.environ.get("SEED_USER_EMAIL", "seed_user@example.com")
    password = os.environ.get("SEED_USER_PASSWORD", "password123")
    full_name = os.environ.get("SEED_USER_FULLNAME", "Seed User")

    user = create_test_user(email=email, password=password, full_name=full_name)
    print("--- Credentials ---")
    print(f"email: {email}")
    print(f"password: {password}")
    print("Use /auth/login (form) to obtain access_token")
