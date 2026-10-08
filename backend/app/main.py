import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from app.core.config import settings
from app.db.session import engine, Base, SessionLocal
from app.models.models import User, Restaurant, FoodItem
from app.core.security import hash_password
from app.api import auth, restaurants, cart, orders, audit

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Secure Online Food Ordering Platform — Software Engineering Lab Implementation"
)

# CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: https://fonts.googleapis.com https://fonts.gstatic.com;"
    return response

# Include API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(restaurants.router, prefix=settings.API_V1_STR)
app.include_router(cart.router, prefix=settings.API_V1_STR)
app.include_router(orders.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "QuickBite",
        "version": settings.VERSION,
        "security_controls": "enforced"
    }

# Automatic Database Seed for Exam/Demo Readiness
def seed_database():
    db = SessionLocal()
    try:
        # Check if users already exist
        if db.query(User).count() == 0:
            print("[INFO] Seeding initial demo data for QuickBite...")

            # 1. Create Restaurants
            rest1 = Restaurant(
                name="Bella Italia Trattoria",
                cuisine_type="Italian",
                address="45 Roma Way, Downtown",
                phone="555-0191",
                is_active=True
            )
            rest2 = Restaurant(
                name="Spice Craft Bistro",
                cuisine_type="Modern Indian",
                address="108 Curry Lane, Uptown",
                phone="555-0192",
                is_active=True
            )
            db.add_all([rest1, rest2])
            db.commit()
            db.refresh(rest1)
            db.refresh(rest2)

            # 2. Create Users
            admin_user = User(
                email="admin@quickbite.com",
                password_hash=hash_password("Admin@123"),
                full_name="QuickBite Administrator",
                role="admin",
                phone="555-0001"
            )
            staff1 = User(
                email="staff1@quickbite.com",
                password_hash=hash_password("Staff@123"),
                full_name="Marco Rossi (Chef)",
                role="restaurant_staff",
                restaurant_id=rest1.id,
                phone="555-0002"
            )
            staff2 = User(
                email="staff2@quickbite.com",
                password_hash=hash_password("Staff@123"),
                full_name="Rajesh Kumar (Kitchen)",
                role="restaurant_staff",
                restaurant_id=rest2.id,
                phone="555-0003"
            )
            alice = User(
                email="alice@customer.com",
                password_hash=hash_password("Customer@123"),
                full_name="Alice Diner",
                role="customer",
                phone="555-0004"
            )
            bob = User(
                email="bob@customer.com",
                password_hash=hash_password("Customer@123"),
                full_name="Bob Foodie",
                role="customer",
                phone="555-0005"
            )
            db.add_all([admin_user, staff1, staff2, alice, bob])
            db.commit()

            # 3. Create Canonical Food Items
            items = [
                # Bella Italia
                FoodItem(restaurant_id=rest1.id, name="Woodfired Margherita Pizza", description="Fresh mozzarella, San Marzano tomatoes, and basil", canonical_price=14.99, category="Pizza", is_available=True),
                FoodItem(restaurant_id=rest1.id, name="Black Truffle Tagliatelle", description="Handmade pasta with creamy black truffle emulsion", canonical_price=18.50, category="Pasta", is_available=True),
                FoodItem(restaurant_id=rest1.id, name="Classic Tiramisu", description="Espresso soaked ladyfingers with mascarpone", canonical_price=7.00, category="Dessert", is_available=True),
                # Spice Craft
                FoodItem(restaurant_id=rest2.id, name="Smoked Butter Chicken", description="Tender chicken tikka in velvet makhani sauce", canonical_price=16.00, category="Curry", is_available=True),
                FoodItem(restaurant_id=rest2.id, name="Garlic Herb Naan", description="Fresh tandoori baked flatbread brushed with ghee", canonical_price=3.50, category="Breads", is_available=True),
                FoodItem(restaurant_id=rest2.id, name="Alphonso Mango Lassi", description="Chilled yogurt smoothie with ripe mango puree", canonical_price=4.50, category="Beverages", is_available=True),
            ]
            db.add_all(items)
            db.commit()
            print("[INFO] Database successfully seeded with demo accounts and restaurants.")
    finally:
        db.close()

seed_database()


# Mount Frontend static files if directory exists
frontend_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend"
)
if os.path.exists(frontend_dir):
    @app.get("/login")
    def get_login_page():
        login_file = os.path.join(frontend_dir, "login.html")
        if os.path.exists(login_file):
            return FileResponse(login_file)
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/register")
    def get_register_page():
        reg_file = os.path.join(frontend_dir, "register.html")
        if os.path.exists(reg_file):
            return FileResponse(reg_file)
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

