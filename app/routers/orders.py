from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.database import engine
from app.auth import get_current_user
from app.models import CartItem, Product, Order, OrderItem
from app.schemas import OrderOut, OrderItemOut

router = APIRouter()

@router.post("/", response_model=OrderOut)
def create_order(user=Depends(get_current_user)):
    with Session(engine) as session:
        cart_statement = select(CartItem).where(CartItem.user_id == user.id)
        cart_items = session.exec(cart_statement).all()
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")
        total = 0.0
        # check stock
        for ci in cart_items:
            prod = session.get(Product, ci.product_id)
            if prod.stock < ci.quantity:
                raise HTTPException(status_code=400, detail=f"Insufficient stock for product {prod.id}")
            total += prod.price * ci.quantity
        order = Order(user_id=user.id, total=total, status="created")
        session.add(order)
        session.commit()
        session.refresh(order)
        items_out = []
        for ci in cart_items:
            prod = session.get(Product, ci.product_id)
            oi = OrderItem(order_id=order.id, product_id=prod.id, quantity=ci.quantity, price=prod.price)
            session.add(oi)
            prod.stock -= ci.quantity
            session.delete(ci)
            items_out.append(oi)
        session.commit()
        # reload order items
        statement = select(OrderItem).where(OrderItem.order_id == order.id)
        stored_items = session.exec(statement).all()
        return {"id": order.id, "user_id": order.user_id, "total": order.total, "status": order.status, "created_at": order.created_at, "items": [{"product_id": it.product_id, "quantity": it.quantity, "price": it.price} for it in stored_items]}

@router.get("/", response_model=List[OrderOut])
def list_orders(user=Depends(get_current_user)):
    with Session(engine) as session:
        statement = select(Order).where(Order.user_id == user.id)
        return session.exec(statement).all()

@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, user=Depends(get_current_user)):
    with Session(engine) as session:
        order = session.get(Order, order_id)
        if not order or order.user_id != user.id:
            raise HTTPException(status_code=404, detail="Order not found")
        statement = select(OrderItem).where(OrderItem.order_id == order.id)
        items = session.exec(statement).all()
        return {"id": order.id, "user_id": order.user_id, "total": order.total, "status": order.status, "created_at": order.created_at, "items": [{"product_id": it.product_id, "quantity": it.quantity, "price": it.price} for it in items]}
