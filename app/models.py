import logging

from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String, Integer, Float, UniqueConstraint, CheckConstraint
from datetime import datetime, timezone
from pydantic import validator


logger = logging.getLogger("autoshop.models")


def now_utc():
	return datetime.now(timezone.utc)

class DomainError(Exception):
	pass

class OutOfStockError(DomainError):
	pass

class ValidationError(DomainError):
	pass

class Category(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	name: str = Field(...)
	description: Optional[str] = None
	products: List["Product"] = Relationship(back_populates="category")


class Product(SQLModel, table=True):
	__table_args__ = (
		CheckConstraint("price >= 0", name="ck_product_price_non_negative"),
	)

	id: Optional[int] = Field(default=None, primary_key=True)
	name: str = Field(sa_column=Column(String(length=200), nullable=False, index=True))
	description: Optional[str] = None
	price: float = Field(default=0.0, sa_column=Column(Float, nullable=False))
	stock: int = Field(default=0)
	category_id: Optional[int] = Field(default=None, foreign_key="category.id")
	category: Optional[Category] = Relationship(back_populates="products")
	created_at: datetime = Field(default_factory=now_utc)

	def reserve(self, qty: int) -> None:
		logger.debug("Reserving %s of product %s (stock=%s)", qty, self.id, self.stock)
		if qty <= 0:
			raise ValidationError("Число должно быть положительных")
		if self.stock is None or self.stock < qty:
			raise OutOfStockError(f"Недостаточное количество {self.id}")
		self.stock -= qty

	def release(self, qty: int) -> None:
		logger.debug("Releasing %s of product %s", qty, self.id)
		if qty <= 0:
			return
		if self.stock is None:
			self.stock = qty
		else:
			self.stock += qty

	@validator("price")
	def price_must_be_non_negative(cls, v):
		if v is None:
			return 0.0
		if v < 0:
			raise ValueError("Цена должна быть >= 0")
		return v

	@validator("stock")
	def stock_must_be_int_and_non_negative(cls, v):
		if v is None:
			return 0
		try:
			iv = int(v)
		except Exception:
			raise ValidationError("Значение должно быть целым числом")
		if iv < 0:
			raise ValidationError("Не может быть отрицательным")
		return iv

	@property
	def available(self) -> bool:
		return bool((self.stock or 0) > 0)


class User(SQLModel, table=True):
	__table_args__ = (UniqueConstraint("email", name="uq_user_email"),)

	id: Optional[int] = Field(default=None, primary_key=True)
	email: str = Field(index=True)
	hashed_password: str
	full_name: Optional[str] = None
	is_active: bool = True
	created_at: datetime = Field(default_factory=now_utc)
	cart_items: List["CartItem"] = Relationship(back_populates="user")
	orders: List["Order"] = Relationship(back_populates="user")
	reviews: List["Review"] = Relationship(back_populates="user")

	def display_name(self) -> str:
		if self.full_name:
			return self.full_name
		local = (self.email or "").split("@")[0]
		return local.replace('.', ' ').title()


class CartItem(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	user_id: int = Field(foreign_key="user.id")
	product_id: int = Field(foreign_key="product.id")
	quantity: int = Field(default=1)
	user: Optional[User] = Relationship(back_populates="cart_items")
	product: Optional[Product] = Relationship()

	@validator("quantity")
	def quantity_positive(cls, v):
		if v is None:
			return 1
		try:
			iv = int(v)
		except Exception:
			raise ValidationError("Количество должно быть целым числом")
		if iv < 1:
			raise ValidationError("Количество должно быть >= 1")
		return iv


class OrderItem(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	order_id: Optional[int] = Field(default=None, foreign_key="order.id")
	product_id: int = Field(foreign_key="product.id")
	quantity: int = Field(default=1)
	price: float = Field(default=0.0)

	@validator("quantity")
	def order_quantity_positive(cls, v):
		if v is None:
			return 1
		iv = int(v)
		if iv < 1:
			raise ValidationError("Количество должно быть положительным")
		return iv

	@validator("price")
	def order_price_non_negative(cls, v):
		if v is None:
			return 0.0
		fv = float(v)
		if fv < 0:
			raise ValueError("Цена должна быть >= 0")
		return fv


class Order(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	user_id: int = Field(foreign_key="user.id")
	total: float = Field(default=0.0)
	status: str = "created"
	created_at: datetime = Field(default_factory=now_utc)
	user: Optional[User] = Relationship(back_populates="orders")
	items: List[OrderItem] = Relationship()

	def recalc_total(self):
		total = 0.0
		for it in getattr(self, "items", []) or []:
			try:
				total += (float(it.price) or 0.0) * int(it.quantity)
			except Exception:
				logger.warning("Bad order item data: %s", it)
		self.total = total
		return self.total

	def place(self, session):
		logger.info("Placing order for user %s", self.user_id)
		for it in getattr(self, "items", []) or []:
			prod = it.product or session.get(Product, it.product_id)
			if prod is None:
				raise ValidationError(f"Товар {it.product_id} не найден")
			prod.reserve(int(it.quantity))
			session.add(prod)
		self.recalc_total()
		self.status = "placed"
		session.add(self)


class Review(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	user_id: int = Field(foreign_key="user.id")
	product_id: int = Field(foreign_key="product.id")
	rating: int = Field(default=5)
	text: Optional[str] = None
	created_at: datetime = Field(default_factory=now_utc)
	user: Optional[User] = Relationship(back_populates="reviews")
	product: Optional[Product] = Relationship()

	@validator("rating")
	def rating_in_range(cls, v):
		if v is None:
			return 5
		try:
			iv = int(v)
		except Exception:
			raise ValidationError("Рейтинг должен быть целым числом")
		if iv < 1 or iv > 5:
			raise ValidationError("Рейтинг должен быть между 1 и 5")
		return iv

