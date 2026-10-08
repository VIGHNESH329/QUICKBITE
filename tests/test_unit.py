import pytest
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.services.pricing import AuthoritativePricingEngine
from app.services.payment import TokenizedPaymentGatewayAdapter
from app.schemas.schemas import SecureOrderItemInputDTO
from app.models.models import FoodItem, Restaurant
from app.db.session import SessionLocal, Base, engine

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_password_hashing_and_verification():
    raw_password = "SecurePassword@123"
    hashed = hash_password(raw_password)
    assert hashed != raw_password
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword@123", hashed) is False

def test_jwt_token_generation_and_decoding():
    payload = {"sub": "42", "role": "customer", "email": "test@quickbite.com"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "42"
    assert decoded["role"] == "customer"
    assert "exp" in decoded

def test_payment_token_gateway_adapter():
    # Valid token
    res_valid = TokenizedPaymentGatewayAdapter.process_charge("tok_visa_4242", 25.50, "alice@customer.com")
    assert res_valid.success is True
    assert res_valid.transaction_reference.startswith("tx_qb_")
    assert "****" in res_valid.masked_token

    # Declined token
    res_declined = TokenizedPaymentGatewayAdapter.process_charge("tok_card_declined", 25.50, "alice@customer.com")
    assert res_declined.success is False
    assert "declined" in res_declined.message.lower()

    # Invalid token format
    res_invalid = TokenizedPaymentGatewayAdapter.process_charge("raw_card_1234567890", 25.50, "alice@customer.com")
    assert res_invalid.success is False
    assert "must begin with 'tok_'" in res_invalid.message

def test_authoritative_pricing_engine_overrides_client(db_session):
    # Ensure restaurant and items exist in DB
    rest = db_session.query(Restaurant).first()
    assert rest is not None, "Database must have at least one restaurant"

    items = db_session.query(FoodItem).filter(FoodItem.restaurant_id == rest.id, FoodItem.is_available == True).all()
    assert len(items) >= 2, "Restaurant must have at least two items"

    item1, item2 = items[0], items[1]
    expected_subtotal = round(item1.canonical_price * 2 + item2.canonical_price * 1, 2)
    expected_tax = round(expected_subtotal * 0.10, 2)
    expected_total = round(expected_subtotal + expected_tax + 3.00, 2)

    order_inputs = [
        SecureOrderItemInputDTO(food_item_id=item1.id, quantity=2),
        SecureOrderItemInputDTO(food_item_id=item2.id, quantity=1)
    ]

    persisted_items, subtotal, tax, delivery, grand_total = AuthoritativePricingEngine.calculate_order_totals(
        db=db_session,
        restaurant_id=rest.id,
        requested_items=order_inputs
    )

    assert subtotal == expected_subtotal
    assert tax == expected_tax
    assert delivery == 3.00
    assert grand_total == expected_total
    assert len(persisted_items) == 2
