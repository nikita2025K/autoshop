from sqlmodel import SQLModel, create_engine
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./app.db")
engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    SQLModel.metadata.create_all(engine)
