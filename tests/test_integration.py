import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.models.models import User, Restaurant, FoodItem, Order, AuditLog
from app.db.session import SessionLocal

client = TestClient(app)

@pytest.fixture(scope="module")
def integration_context():
    db = SessionLocal()
    alice = db.query(User).filter(User.email == "alice@customer.com").first()
    staff1 = db.query(User).filter(User.email == "staff1@quickbite.com").first()
    admin = db.query(User).filter(User.email == "admin@quickbite.com").first()
    rest1 = db.query(Restaurant).filter(Restaurant.id == 1).first()
    item1 = db.query(FoodItem).filter(FoodItem.restaurant_id == rest1.id, FoodItem.is_available == True).first()

    alice_token = create_access_token({"sub": str(alice.id), "role": "customer", "email": alice.email})
    staff1_token = create_access_token({"sub": str(staff1.id), "role": "restaurant_staff", "email": staff1.email, "restaurant_id": rest1.id})
    admin_token = create_access_token({"sub": str(admin.id), "role": "admin", "email": admin.email})

    db.close()
    return {
        "alice": alice,
        "staff1": staff1,
        "admin": admin,
        "rest1": rest1,
        "item1": item1,
        "alice_token": alice_token,
        "staff1_token": staff1_token,
        "admin_token": admin_token,
    }

def test_price_tampering_attempt_is_strictly_neutralized(integration_context):
    ctx = integration_context
    # Malicious client sends price=0.01 and total_amount=0.01 in the payload
    # The server schema and pricing engine must ignore/reject any client pricing
    malicious_payload = {
        "restaurant_id": ctx["rest1"].id,
        "items": [
            {
                "food_item_id": ctx["item1"].id,
                "quantity": 2,
                "price": 0.01,         # Injected client price
                "unit_price": 0.01      # Injected client unit price
            }
        ],
        "delivery_address": "888 Secure Way, Suite 100",
        "payment_token": "tok_visa_valid",
        "total_amount": 0.01,          # Injected grand total
        "subtotal": 0.01
    }

    res = client.post(
        "/api/orders",
        json=malicious_payload,
        headers={"Authorization": f"Bearer {ctx['alice_token']}"}
    )

    assert res.status_code == 201
    data = res.json()
    order_id = data["id"]

    # Canonical calculation: 2 * canonical_price + 10% tax + 3.00 flat delivery
    expected_subtotal = round(ctx["item1"].canonical_price * 2, 2)
    expected_tax = round(expected_subtotal * 0.10, 2)
    expected_total = round(expected_subtotal + expected_tax + 3.00, 2)

    assert data["total_amount"] == expected_total
    assert data["total_amount"] != 0.01
    assert data["subtotal_amount"] == expected_subtotal

def test_unauthenticated_request_rejected(integration_context):
    # Attempting to access protected endpoints without Bearer token must return 401
    res = client.get("/api/orders")
    assert res.status_code == 401
    assert "Missing Authorization Bearer token" in res.json()["detail"] or "unauthorized" in res.json()["detail"].lower()

def test_registration_role_privilege_escalation_rejected():
    # Attempting to self-register as restaurant_staff or admin must fail validation
    malicious_register = {
        "full_name": "Attacker Impersonator",
        "email": "attacker_admin@fake.com",
        "password": "Password@123",
        "role": "admin"
    }
    res = client.post("/api/auth/register", json=malicious_register)
    assert res.status_code == 422
    assert "customer" in str(res.json()).lower()

def test_complete_order_lifecycle_fsm_progression(integration_context):
    ctx = integration_context
    # 1. Place order
    res_place = client.post(
        "/api/orders",
        json={
            "restaurant_id": ctx["rest1"].id,
            "items": [{"food_item_id": ctx["item1"].id, "quantity": 1}],
            "delivery_address": "404 FSM Boulevard",
            "payment_token": "tok_visa_valid"
        },
        headers={"Authorization": f"Bearer {ctx['alice_token']}"}
    )
    assert res_place.status_code == 201
    order_id = res_place.json()["id"]
    assert res_place.json()["status"] == "PLACED"

    # 2. Staff accepts
    res_acc = client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": "ACCEPTED"},
        headers={"Authorization": f"Bearer {ctx['staff1_token']}"}
    )
    assert res_acc.status_code == 200
    assert res_acc.json()["status"] == "ACCEPTED"

    # 3. Staff prepares
    res_prep = client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": "PREPARING"},
        headers={"Authorization": f"Bearer {ctx['staff1_token']}"}
    )
    assert res_prep.status_code == 200
    assert res_prep.json()["status"] == "PREPARING"

    # 4. Out for delivery
    res_out = client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": "OUT_FOR_DELIVERY"},
        headers={"Authorization": f"Bearer {ctx['staff1_token']}"}
    )
    assert res_out.status_code == 200
    assert res_out.json()["status"] == "OUT_FOR_DELIVERY"

    # 5. Delivered
    res_del = client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": "DELIVERED"},
        headers={"Authorization": f"Bearer {ctx['staff1_token']}"}
    )
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "DELIVERED"

    # 6. Illegal backward transition (DELIVERED -> PREPARING)
    res_illegal = client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": "PREPARING"},
        headers={"Authorization": f"Bearer {ctx['staff1_token']}"}
    )
    assert res_illegal.status_code == 400
    assert "illegal state transition" in res_illegal.json()["detail"].lower()

def test_tamper_evident_audit_log_generation(integration_context):
    ctx = integration_context
    # Admin inspects audit ledger
    res = client.get(
        "/api/audit/logs",
        headers={"Authorization": f"Bearer {ctx['admin_token']}"}
    )
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) > 0
    actions = [l["action_type"] for l in logs]
    assert any("ORDER" in a for a in actions)
