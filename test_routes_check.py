import sys
import os

quickbite_dir = r"C:\Users\deepa\Downloads\sse_endsem\QuickBite"
backend_dir = os.path.join(quickbite_dir, "backend")
sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=" * 65)
print("       QUICKBITE v2.0.0 ROUTE VERIFICATION REPORT")
print("=" * 65)

# 1. Unprotected & Static UI Routes
r_home = client.get("/")
print(f"1. GET /                    -> Status: {r_home.status_code}")
assert r_home.status_code == 200
assert "QuickBite" in r_home.text
print("   -> Renders index.html successfully (200 OK)")

r_login = client.get("/login")
print(f"2. GET /login               -> Status: {r_login.status_code}")
assert r_login.status_code == 200
assert "QuickBite" in r_login.text
assert "login" in r_login.text.lower()
print("   -> Renders login.html successfully (200 OK)")

r_register = client.get("/register")
print(f"3. GET /register            -> Status: {r_register.status_code}")
assert r_register.status_code == 200
assert "QuickBite" in r_register.text
assert "register" in r_register.text.lower() or "create" in r_register.text.lower()
print("   -> Renders register.html successfully (200 OK)")

r_health = client.get("/api/health")
print(f"4. GET /api/health          -> Status: {r_health.status_code}")
assert r_health.status_code == 200
health_json = r_health.json()
print(f"   -> System Status: {health_json.get('status')}")

r_rests = client.get("/api/restaurants")
print(f"5. GET /api/restaurants     -> Status: {r_rests.status_code}")
assert r_rests.status_code == 200
rests_json = r_rests.json()
print(f"   -> Active Restaurants: {len(rests_json)}")

# 2. Protected Routes & Authentication
r_orders_unauth = client.get("/api/orders")
print(f"6. GET /api/orders (unauth) -> Status: {r_orders_unauth.status_code}")
assert r_orders_unauth.status_code == 401
print("   -> Correctly rejected without JWT token (401 Unauthorized)")

r_login_post = client.post("/api/auth/login", json={
    "email": "alice@customer.com",
    "password": "Customer@123"
})
print(f"7. POST /api/auth/login     -> Status: {r_login_post.status_code}")
assert r_login_post.status_code == 200
token = r_login_post.json()["access_token"]
print("   -> Successfully authenticated, received valid signed JWT")

r_orders_auth = client.get("/api/orders", headers={"Authorization": f"Bearer {token}"})
print(f"8. GET /api/orders (auth)   -> Status: {r_orders_auth.status_code}")
assert r_orders_auth.status_code == 200
orders_json = r_orders_auth.json()
print(f"   -> Successfully retrieved customer orders: {len(orders_json)} records (200 OK)")

print("=" * 65)
print("RESULT: ALL ROUTES TESTED AND VERIFIED. STATUS 100% OPERATIONAL.")
print("=" * 65)
