import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.models.models import User, Restaurant, FoodItem, Order
from app.db.session import SessionLocal

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_test_users():
    db = SessionLocal()
    alice = db.query(User).filter(User.email == "alice@customer.com").first()
    bob = db.query(User).filter(User.email == "bob@customer.com").first()
    staff1 = db.query(User).filter(User.email == "staff1@quickbite.com").first()
    staff2 = db.query(User).filter(User.email == "staff2@quickbite.com").first()
    rest1 = db.query(Restaurant).filter(Restaurant.id == 1).first()
    rest2 = db.query(Restaurant).filter(Restaurant.id == 2).first()
    item1 = db.query(FoodItem).filter(FoodItem.restaurant_id == rest1.id).first()

    alice_token = create_access_token({"sub": str(alice.id), "role": "customer", "email": alice.email})
    bob_token = create_access_token({"sub": str(bob.id), "role": "customer", "email": bob.email})
    staff1_token = create_access_token({"sub": str(staff1.id), "role": "restaurant_staff", "email": staff1.email, "restaurant_id": rest1.id})
    staff2_token = create_access_token({"sub": str(staff2.id), "role": "restaurant_staff", "email": staff2.email, "restaurant_id": rest2.id})

    db.close()
    return {
        "alice": alice,
        "bob": bob,
        "staff1": staff1,
        "staff2": staff2,
        "rest1": rest1,
        "rest2": rest2,
        "item1": item1,
        "alice_token": alice_token,
        "bob_token": bob_token,
        "staff1_token": staff1_token,
        "staff2_token": staff2_token,
    }

def test_customer_order_ownership_bola_protection(setup_test_users):
    data = setup_test_users
    # Step 1: Alice creates an order
    order_payload = {
        "restaurant_id": data["rest1"].id,
        "items": [{"food_item_id": data["item1"].id, "quantity": 1}],
        "delivery_address": "123 Alice St, Apt 4B",
        "payment_token": "tok_visa_valid"
    }
    res_create = client.post(
        "/api/orders",
        json=order_payload,
        headers={"Authorization": f"Bearer {data['alice_token']}"}
    )
    assert res_create.status_code == 201
    order_id = res_create.json()["id"]

    # Step 2: Alice can read her own order
    res_alice_read = client.get(
        f"/api/orders/{order_id}",
        headers={"Authorization": f"Bearer {data['alice_token']}"}
    )
    assert res_alice_read.status_code == 200
    assert res_alice_read.json()["id"] == order_id

    # Step 3: Bob attempts to read Alice's order (BOLA Attack)
    res_bob_read = client.get(
        f"/api/orders/{order_id}",
        headers={"Authorization": f"Bearer {data['bob_token']}"}
    )
    assert res_bob_read.status_code == 403
    assert "access denied" in res_bob_read.json()["detail"].lower()

    # Step 4: Bob attempts to cancel Alice's order (IDOR Attack)
    res_bob_cancel = client.post(
        f"/api/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {data['bob_token']}"}
    )
    assert res_bob_cancel.status_code == 403
    assert "access denied" in res_bob_cancel.json()["detail"].lower()

def test_restaurant_staff_tenant_isolation(setup_test_users):
    data = setup_test_users
    # Create order at Restaurant 1
    order_payload = {
        "restaurant_id": data["rest1"].id,
        "items": [{"food_item_id": data["item1"].id, "quantity": 1}],
        "delivery_address": "450 Market St",
        "payment_token": "tok_visa_valid"
    }
    res_create = client.post(
        "/api/orders",
        json=order_payload,
        headers={"Authorization": f"Bearer {data['alice_token']}"}
    )
    assert res_create.status_code == 201
    order_id = res_create.json()["id"]

    # Staff 2 (from Restaurant 2) attempts to accept Restaurant 1's order
    res_cross_tenant = client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": "ACCEPTED"},
        headers={"Authorization": f"Bearer {data['staff2_token']}"}
    )
    assert res_cross_tenant.status_code == 403
    assert "only manage orders for your assigned restaurant" in res_cross_tenant.json()["detail"].lower()

def test_order_cancellation_state_machine_invariant(setup_test_users):
    data = setup_test_users
    # Create order
    res_create = client.post(
        "/api/orders",
        json={
            "restaurant_id": data["rest1"].id,
            "items": [{"food_item_id": data["item1"].id, "quantity": 1}],
            "delivery_address": "777 Sunset Blvd",
            "payment_token": "tok_visa_valid"
        },
        headers={"Authorization": f"Bearer {data['alice_token']}"}
    )
    order_id = res_create.json()["id"]

    # Staff 1 accepts order
    res_accept = client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": "ACCEPTED"},
        headers={"Authorization": f"Bearer {data['staff1_token']}"}
    )
    assert res_accept.status_code == 200

    # Alice attempts to cancel accepted order
    res_cancel = client.post(
        f"/api/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {data['alice_token']}"}
    )
    assert res_cancel.status_code == 400
    assert "cannot be cancelled" in res_cancel.json()["detail"].lower()
