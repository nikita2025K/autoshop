from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.db.database import init_db
from app.routers import auth, products, categories, cart, orders, reviews, users

app = FastAPI(title="Autoshop API")

# include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"]) 
app.include_router(products.router, prefix="/products", tags=["products"]) 
app.include_router(categories.router, prefix="/categories", tags=["categories"]) 
app.include_router(cart.router, prefix="/cart", tags=["cart"]) 
app.include_router(orders.router, prefix="/orders", tags=["orders"]) 
app.include_router(reviews.router, prefix="/reviews", tags=["reviews"]) 
app.include_router(users.router, prefix="/users", tags=["users"])


@app.on_event("startup")
async def on_startup():
    init_db()



@app.get("/", include_in_schema=False)
def root():
    """Redirect root to the interactive docs."""
    return RedirectResponse(url="/docs")

