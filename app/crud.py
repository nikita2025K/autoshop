from typing import List, Optional
from sqlmodel import Session, select
from app.db.database import engine
from app.models import Product, Category, User, CartItem, Order, OrderItem, Review


def get_product(product_id: int) -> Optional[Product]:
    with Session(engine) as session:
        return session.get(Product, product_id)

def list_products(skip: int = 0, limit: int = 100):
    with Session(engine) as session:
        statement = select(Product).offset(skip).limit(limit)
        return session.exec(statement).all()


def get_category(category_id: int) -> Optional[Category]:
    with Session(engine) as session:
        return session.get(Category, category_id)

def list_categories():
    with Session(engine) as session:
        statement = select(Category)
        return session.exec(statement).all()

def get_cart_items_for_user(user_id: int):
    with Session(engine) as session:
        statement = select(CartItem).where(CartItem.user_id == user_id)
        return session.exec(statement).all()

def get_reviews_for_product(product_id: int):
    with Session(engine) as session:
        statement = select(Review).where(Review.product_id == product_id)
        return session.exec(statement).all()
