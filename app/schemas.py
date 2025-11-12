from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, validator, root_validator, Field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import logging

logger = logging.getLogger("autoshop.schemas")


class BaseOut(BaseModel):
    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

    @validator("password")
    def password_strength(cls, v: str) -> str:
        if v.isalpha() or v.isdigit():
            raise ValueError("Пароль должен содержать буквы и цифры")
        if "password" in v.lower():
            raise ValueError("Пароль слишком простой")
        return v

    @validator("email")
    def email_domain_check(cls, v: EmailStr) -> EmailStr:
        domain = v.split("@")[-1].lower()
        banned_suffixes = ("tempmail.com", "disposable.test")
        if any(domain.endswith(s) for s in banned_suffixes):
            raise ValueError("Пожалуйста используйте настояющую электронную почту")
        return v


class UserOut(BaseOut):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    created_at: datetime

    def masked_email(self) -> str:
        local, _, domain = self.email.partition("@")
        if len(local) <= 2:
            masked = "*"
        else:
            masked = local[0] + "*" * (len(local) - 2) + local[-1]
        return f"{masked}@{domain}"


class Token(BaseModel):
    access_token: str
    token_type: str = Field("Bearer", description="token type, usually 'Bearer'")


class CategoryOut(BaseOut):
    id: int
    name: str
    description: Optional[str]

    @property
    def short_name(self) -> str:
        return (self.name[:30] + "…") if len(self.name) > 30 else self.name


class ProductOut(BaseOut):
    id: int
    name: str
    description: Optional[str]
    price: Decimal
    stock: int
    category_id: Optional[int]
    created_at: datetime

    @validator("price", pre=True, always=True)
    def normalize_price(cls, v):
        try:
            d = Decimal(v)
        except Exception:
            raise ValueError("Неправильный формат цены")
        return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class ProductCreate(BaseModel):
    name: str
    description: Optional[str]
    price: Decimal
    stock: int = 0
    category_id: Optional[int]

    @validator("price")
    def min_price(cls, v: Decimal) -> Decimal:
        if v < Decimal("0.50"):
            raise ValueError("Минимально возможная стоимость равна 0.50")
        return v

    @validator("stock")
    def stock_limits(cls, v: int) -> int:
        if v is None:
            return 0
        if v > 100000:
            logger.warning("stock value %s exceeds soft cap, clamping to 100000", v)
            return 100000
        return v


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int

    @validator("quantity")
    def quantity_range(cls, v: int) -> int:
        if v is None:
            return 1
        if v < 1 or v > 100:
            raise ValueError("Количество должно быть между 1 и 100")
        return v


class CartItemOut(BaseOut):
    id: int
    product: ProductOut
    quantity: int
    subtotal: Decimal

    @root_validator(pre=True)
    def compute_subtotal(cls, values):
        prod = values.get("product")
        qty = values.get("quantity") or 0
        try:
            price = Decimal(getattr(prod, "price", "0"))
            values["subtotal"] = (price * Decimal(qty)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except Exception:
            values["subtotal"] = Decimal("0.00")
        return values


class OrderItemOut(BaseOut):
    product_id: int
    quantity: int
    price: Decimal


class OrderOut(BaseOut):
    id: int
    user_id: int
    total: Decimal
    status: Literal["created", "placed", "shipped", "cancelled"]
    created_at: datetime
    items: List[OrderItemOut]


class ReviewCreate(BaseModel):
    rating: int
    text: Optional[str]

    @validator("text")
    def text_length_hint(cls, v):
        if v and len(v) > 2000:
            raise ValueError("Отзыв слишком длинный, введите менее 2000 символов")
        return v

    @validator("rating")
    def rating_feedback_hint(cls, v):
        if v < 1 or v > 5:
            raise ValueError("Пожалуйста, оценивайте товар от 1 до 5")
        if v <= 2:
            logger.info("Low rating submitted: %s — consider prompting user for details", v)
        return v


class ReviewOut(BaseOut):
    id: int
    user_id: int
    product_id: int
    rating: int
    text: Optional[str]
    created_at: datetime


class ProfileUpdate(BaseModel):
    full_name: Optional[str]
    email: Optional[EmailStr]

    @validator("full_name")
    def strip_full_name(cls, v):
        return v.strip() if isinstance(v, str) else v
