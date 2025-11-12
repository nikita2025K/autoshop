from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.database import engine
from app.auth import get_current_user
from app.models import Review, Product
from app.schemas import ReviewCreate, ReviewOut

router = APIRouter()

@router.post("/products/{product_id}", response_model=ReviewOut)
def add_review(product_id: int, r: ReviewCreate, user=Depends(get_current_user)):
    with Session(engine) as session:
        prod = session.get(Product, product_id)
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found")
        review = Review(user_id=user.id, product_id=product_id, rating=r.rating, text=r.text)
        session.add(review)
        session.commit()
        session.refresh(review)
        return review

@router.get("/products/{product_id}", response_model=list[ReviewOut])
def list_reviews(product_id: int):
    with Session(engine) as session:
        statement = select(Review).where(Review.product_id == product_id)
        return session.exec(statement).all()

@router.put("/{review_id}", response_model=ReviewOut)
def edit_review(review_id: int, r: ReviewCreate, user=Depends(get_current_user)):
    with Session(engine) as session:
        review = session.get(Review, review_id)
        if not review or review.user_id != user.id:
            raise HTTPException(status_code=404, detail="Review not found")
        review.rating = r.rating
        review.text = r.text
        session.add(review)
        session.commit()
        session.refresh(review)
        return review

@router.delete("/{review_id}", status_code=204)
def delete_review(review_id: int, user=Depends(get_current_user)):
    with Session(engine) as session:
        review = session.get(Review, review_id)
        if not review or review.user_id != user.id:
            raise HTTPException(status_code=404, detail="Review not found")
        session.delete(review)
        session.commit()
        return None
