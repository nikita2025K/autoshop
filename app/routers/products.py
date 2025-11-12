from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from sqlmodel import select, Session

from app.db.database import engine
from app.models import Product
from app.schemas import ProductOut, ProductCreate

router = APIRouter()

@router.get("/", response_model=List[ProductOut])
def list_products(page: int = 1, size: int = 20, category_id: Optional[int] = None, q: Optional[str] = None):
    skip = (page - 1) * size
    with Session(engine) as session:
        statement = select(Product)
        if category_id:
            statement = statement.where(Product.category_id == category_id)
        if q:
            qexpr = f"%{q}%"
            statement = statement.where((Product.name.ilike(qexpr)) | (Product.description.ilike(qexpr)))
        statement = statement.offset(skip).limit(size)
        results = session.exec(statement).all()
        return results

@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int):
    with Session(engine) as session:
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product

@router.get("/search", response_model=List[ProductOut])
def search_products(q: str = Query(..., min_length=1)):
    with Session(engine) as session:
        qexpr = f"%{q}%"
        statement = select(Product).where((Product.name.ilike(qexpr)) | (Product.description.ilike(qexpr)))
        return session.exec(statement).all()
