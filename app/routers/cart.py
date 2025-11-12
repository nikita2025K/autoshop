from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.database import engine
from app.auth import get_current_user
from app.models import CartItem, Product
from app.schemas import CartItemCreate

router = APIRouter()

@router.get("/", response_model=List[dict])
def get_cart(user=Depends(get_current_user)):
    with Session(engine) as session:
        statement = select(CartItem).where(CartItem.user_id == user.id)
        items = session.exec(statement).all()
        out = []
        for it in items:
            prod = session.get(Product, it.product_id)
            out.append({"id": it.id, "product": prod, "quantity": it.quantity, "subtotal": prod.price * it.quantity})
        return out

@router.post("/", status_code=201)
def add_to_cart(item_in: CartItemCreate, user=Depends(get_current_user)):
    with Session(engine) as session:
        product = session.get(Product, item_in.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if item_in.quantity < 1:
            raise HTTPException(status_code=400, detail="Quantity must be >=1")
        statement = select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == item_in.product_id)
        cart_item = session.exec(statement).first()
        if cart_item:
            cart_item.quantity += item_in.quantity
            session.add(cart_item)
        else:
            cart_item = CartItem(user_id=user.id, product_id=item_in.product_id, quantity=item_in.quantity)
            session.add(cart_item)
        session.commit()
        session.refresh(cart_item)
        return {"id": cart_item.id, "product": product, "quantity": cart_item.quantity, "subtotal": product.price * cart_item.quantity}

@router.delete("/{cart_item_id}", status_code=204)
def delete_cart_item(cart_item_id: int, user=Depends(get_current_user)):
    with Session(engine) as session:
        item = session.get(CartItem, cart_item_id)
        if not item or item.user_id != user.id:
            raise HTTPException(status_code=404, detail="Cart item not found")
        session.delete(item)
        session.commit()
        return None
