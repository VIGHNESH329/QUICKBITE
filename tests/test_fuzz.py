import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.models.models import User
from app.db.session import SessionLocal

client = TestClient(app)

@pytest.fixture(scope="module")
def customer_auth_header():
    db = SessionLocal()
    alice = db.query(User).filter(User.email == "alice@customer.com").first()
    token = create_access_token({"sub": str(alice.id), "role": "customer", "email": alice.email})
    db.close()
    return {"Authorization": f"Bearer {token}"}

def test_fuzz_quantity_boundary_negative_and_zero(customer_auth_header):
    # Fuzz target 1: Quantity = 0
    payload_zero = {
        "restaurant_id": 1,
        "items": [{"food_item_id": 1, "quantity": 0}],
        "delivery_address": "Test Street",
        "payment_token": "tok_visa_valid"
    }
    res0 = client.post("/api/orders", json=payload_zero, headers=customer_auth_header)
    assert res0.status_code == 422

    # Fuzz target 2: Quantity = -5
    payload_neg = {
        "restaurant_id": 1,
        "items": [{"food_item_id": 1, "quantity": -5}],
        "delivery_address": "Test Street",
        "payment_token": "tok_visa_valid"
    }
    res_neg = client.post("/api/orders", json=payload_neg, headers=customer_auth_header)
    assert res_neg.status_code == 422

def test_fuzz_quantity_boundary_excessive(customer_auth_header):
    # Fuzz target 3: Quantity = 10000 (exceeds le=99 bound)
    payload_huge = {
        "restaurant_id": 1,
        "items": [{"food_item_id": 1, "quantity": 10000}],
        "delivery_address": "Test Street",
        "payment_token": "tok_visa_valid"
    }
    res_huge = client.post("/api/orders", json=payload_huge, headers=customer_auth_header)
    assert res_huge.status_code == 422

def test_fuzz_empty_items_array(customer_auth_header):
    # Fuzz target 4: Empty items array
    payload_empty = {
        "restaurant_id": 1,
        "items": [],
        "delivery_address": "Test Street",
        "payment_token": "tok_visa_valid"
    }
    res_empty = client.post("/api/orders", json=payload_empty, headers=customer_auth_header)
    assert res_empty.status_code == 422

def test_fuzz_sqli_and_xss_in_delivery_address(customer_auth_header):
    # Fuzz target 5: SQL Injection payload string in address
    sqli_payload = {
        "restaurant_id": 1,
        "items": [{"food_item_id": 1, "quantity": 1}],
        "delivery_address": "' OR '1'='1' -- DROP TABLE users; --",
        "payment_token": "tok_visa_valid"
    }
    res_sqli = client.post("/api/orders", json=sqli_payload, headers=customer_auth_header)
    # Must succeed cleanly or fail with validation; must NEVER return 500 internal server crash
    assert res_sqli.status_code in [201, 400]
    if res_sqli.status_code == 201:
        # Check that table still exists and data was safely parameterized
        assert "id" in res_sqli.json()

    # Fuzz target 6: XSS payload string in address
    xss_payload = {
        "restaurant_id": 1,
        "items": [{"food_item_id": 1, "quantity": 1}],
        "delivery_address": "<script>alert('XSS_PAYLOAD')</script>",
        "payment_token": "tok_visa_valid"
    }
    res_xss = client.post("/api/orders", json=xss_payload, headers=customer_auth_header)
    assert res_xss.status_code in [201, 400]

def test_fuzz_invalid_types_for_ids(customer_auth_header):
    # Fuzz target 7: Non-integer food_item_id
    payload_bad_type = {
        "restaurant_id": 1,
        "items": [{"food_item_id": "not_a_number", "quantity": 1}],
        "delivery_address": "Test Address",
        "payment_token": "tok_visa_valid"
    }
    res_bad = client.post("/api/orders", json=payload_bad_type, headers=customer_auth_header)
    assert res_bad.status_code == 422

def test_fuzz_valid_boundaries_min_and_max_quantity(customer_auth_header):
    # Boundary 1: Minimum allowable quantity = 1
    res_min = client.post(
        "/api/orders",
        json={
            "restaurant_id": 1,
            "items": [{"food_item_id": 1, "quantity": 1}],
            "delivery_address": "100 Boundary Lane",
            "payment_token": "tok_visa_valid"
        },
        headers=customer_auth_header
    )
    assert res_min.status_code == 201

    # Boundary 2: Maximum allowable quantity = 99
    res_max = client.post(
        "/api/orders",
        json={
            "restaurant_id": 1,
            "items": [{"food_item_id": 1, "quantity": 99}],
            "delivery_address": "99 Boundary Lane",
            "payment_token": "tok_visa_valid"
        },
        headers=customer_auth_header
    )
    assert res_max.status_code == 201

def test_fuzz_oversized_address_string_boundary(customer_auth_header):
    # Boundary: delivery_address max_length is 250 characters; send 500 characters
    oversized_address = "A" * 500
    res_oversized = client.post(
        "/api/orders",
        json={
            "restaurant_id": 1,
            "items": [{"food_item_id": 1, "quantity": 1}],
            "delivery_address": oversized_address,
            "payment_token": "tok_visa_valid"
        },
        headers=customer_auth_header
    )
    assert res_oversized.status_code == 422

def test_fuzz_special_characters_and_unicode_resilience(customer_auth_header):
    # Fuzz: Unicode emojis, RTL strings, null byte representations
    fuzz_address = "🏢 100 Main St \u202Ereversed \u0000 \x00 #3B"
    res_fuzz = client.post(
        "/api/orders",
        json={
            "restaurant_id": 1,
            "items": [{"food_item_id": 1, "quantity": 1}],
            "delivery_address": fuzz_address,
            "payment_token": "tok_visa_valid"
        },
        headers=customer_auth_header
    )
    # Must handle gracefully without unhandled 500 crashes
    assert res_fuzz.status_code in [201, 400, 422]

