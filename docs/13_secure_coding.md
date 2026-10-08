# Phase 12: Secure Coding & Vulnerability Refactoring — QuickBite

## 1. Overview of Secure Coding Standards in QuickBite
QuickBite implements defensive programming patterns to counteract the OWASP Top 10 API Security Risks. This phase demonstrates two real-world architectural refactoring cases showing vulnerable implementations, root cause analyses, secure refactored code, and tangible security benefits.

---

## 2. Weakness Demonstration 1: Client-Controlled Order Price (Parameter Tampering)

### 2.1 Vulnerable Implementation (Antipattern)
```python
# VULNERABLE: Trusting pricing and totals supplied by the client
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

class ClientOrderItem(BaseModel):
    item_id: int
    name: str
    price: float   # VULNERABILITY: Client sends the unit price!
    quantity: int

class ClientOrderRequest(BaseModel):
    restaurant_id: int
    items: list[ClientOrderItem]
    total_amount: float  # VULNERABILITY: Client sends the grand total!

@router.post("/api/orders/vulnerable")
def place_order_vulnerable(payload: ClientOrderRequest, current_user = Depends(get_current_user), db = Depends(get_db)):
    # Flaw: The application inserts the order directly using the client's total_amount!
    order = Order(
        customer_id=current_user.id,
        restaurant_id=payload.restaurant_id,
        total_amount=payload.total_amount, # Untrusted input written to financial ledger
        status="PLACED"
    )
    db.add(order)
    db.commit()
    # Process payment using untrusted amount
    charge_customer(user=current_user, amount=payload.total_amount)
    return {"order_id": order.id, "amount_charged": payload.total_amount}
```

### 2.2 Why Vulnerable
- **Root Cause**: Failure to enforce the **Server as Single Source of Truth** for financial data.
- **Attack Scenario**: An attacker uses an intercepting proxy (e.g., OWASP ZAP or Burp Suite) or browser console to tamper with the JSON request:
  ```json
  {
    "restaurant_id": 1,
    "items": [{"item_id": 4, "name": "Gourmet Truffle Steak", "price": 0.01, "quantity": 10}],
    "total_amount": 0.10
  }
  ```
- **Impact**: The restaurant kitchen prepares a $250.00 meal while the payment gateway only charges the attacker 10 cents, causing direct financial fraud.

---

### 2.3 Secure Refactored Implementation (Authoritative Pricing Engine)
```python
# SECURE: Strict server-side recalculation using canonical database prices
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

class SecureOrderItemDTO(BaseModel):
    food_item_id: int = Field(..., gt=0, description="Positive food item ID")
    quantity: int = Field(..., ge=1, le=99, description="Quantity bounded between 1 and 99")

class SecureOrderCreateDTO(BaseModel):
    restaurant_id: int = Field(..., gt=0)
    items: list[SecureOrderItemDTO] = Field(..., min_length=1, max_length=50)
    delivery_address: str = Field(..., min_length=5, max_length=250)
    payment_token: str = Field(..., min_length=10, max_length=100)
    # Notice: NO price or total_amount fields exist in this DTO!

@router.post("/api/orders", response_model=OrderResponseDTO, status_code=status.HTTP_201_CREATED)
def place_order_secure(
    payload: SecureOrderCreateDTO,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Step 1: Verify Restaurant is active
    restaurant = db.query(Restaurant).filter(Restaurant.id == payload.restaurant_id, Restaurant.is_active == True).first()
    if not restaurant:
        raise HTTPException(status_code=400, detail="Target restaurant is inactive or does not exist")

    # Step 2: Fetch canonical items from database
    item_ids = [item.food_item_id for item in payload.items]
    db_items = db.query(FoodItem).filter(
        FoodItem.id.in_(item_ids),
        FoodItem.restaurant_id == payload.restaurant_id,
        FoodItem.is_available == True
    ).all()
    
    if len(db_items) != len(item_ids):
        raise HTTPException(status_code=400, detail="One or more selected items are invalid or unavailable")

    db_item_map = {item.id: item for item in db_items}

    # Step 3: Compute authoritative financial totals server-side
    calculated_subtotal = 0.0
    order_items_to_persist = []

    for item_input in payload.items:
        db_item = db_item_map[item_input.food_item_id]
        unit_price = float(db_item.canonical_price)
        line_cost = unit_price * item_input.quantity
        calculated_subtotal += line_cost

        order_items_to_persist.append(
            OrderItem(
                food_item_id=db_item.id,
                snapshot_unit_price=unit_price,
                quantity=item_input.quantity
            )
        )

    # Calculate tax and delivery fee authoritatively
    tax = round(calculated_subtotal * 0.10, 2)
    delivery_fee = 3.00
    grand_total = round(calculated_subtotal + tax + delivery_fee, 2)

    # Step 4: Execute payment with authoritative amount
    payment_result = PaymentService.process_charge(
        token=payload.payment_token,
        amount=grand_total,
        customer_email=current_user.email
    )
    if not payment_result.success:
        raise HTTPException(status_code=400, detail=f"Payment declined: {payment_result.message}")

    # Step 5: Save order atomically
    new_order = Order(
        customer_id=current_user.id,
        restaurant_id=payload.restaurant_id,
        subtotal_amount=calculated_subtotal,
        tax_amount=tax,
        delivery_fee=delivery_fee,
        total_amount=grand_total,
        delivery_address=payload.delivery_address,
        status="PLACED",
        items=order_items_to_persist
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # Step 6: Log audit event
    AuditService.log(
        db=db,
        user_id=current_user.id,
        action="ORDER_CREATED",
        entity="ORDER",
        entity_id=new_order.id,
        details=f"Order placed with authoritative total: ${grand_total}"
    )

    return new_order
```

### 2.4 Security & Architectural Benefit
- **Complete Elimination of Price Manipulation**: The client payload does not even contain a price field. The database is the sole authority.
- **Quantity Bounds Validation**: Pydantic constraints (`Field(ge=1, le=99)`) reject negative, zero, or overflow integer quantities before business execution.
- **Auditability**: Order total and transaction reference are immutably logged for reconciliation.

---

## 3. Weakness Demonstration 2: Missing Ownership Authorization (BOLA / IDOR)

### 3.1 Vulnerable Implementation (Antipattern)
```python
# VULNERABLE: Direct access to order by ID without verifying customer ownership
@router.post("/api/orders/{order_id}/cancel_vulnerable")
def cancel_order_vulnerable(order_id: int, current_user = Depends(get_current_user), db = Depends(get_db)):
    # Vulnerability: Queries purely by order_id, ignoring who owns it!
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    # Flaw: No check that order.customer_id == current_user.id
    order.status = "CANCELLED"
    db.commit()
    return {"message": "Order cancelled successfully"}
```

### 3.2 Why Vulnerable
- **Root Cause**: Missing Object-Level Access Control (OWASP API Security Top 10 - API1:2023 Broken Object Level Authorization).
- **Attack Scenario**: User Alice logs in and notices her own order has `id: 105`. An attacker, Bob, logs in as himself and sends:
  `POST /api/orders/105/cancel_vulnerable`
  The backend cancels Alice's dinner delivery because it only checks if the caller is an authenticated user, without checking *ownership*.

---

### 3.3 Secure Refactored Implementation (Ownership & State Machine Verification)
```python
# SECURE: Multi-layer ownership verification and state machine check
@router.post("/api/orders/{order_id}/cancel", response_model=OrderResponseDTO)
def cancel_order_secure(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Step 1: Query order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Step 2: Enforce Customer Ownership Check
    # Customer can ONLY cancel their own order; Admin can override if necessary
    if order.customer_id != current_user.id and current_user.role != "admin":
        # Audit the unauthorized attempt
        AuditService.log(
            db=db,
            user_id=current_user.id,
            action="AUTHZ_VIOLATION_CANCEL_ORDER",
            entity="ORDER",
            entity_id=order_id,
            status_result="FAILURE",
            details=f"User {current_user.id} attempted to cancel order owned by {order.customer_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to cancel this order."
        )

    # Step 3: State Machine Validation
    # Cancellation is ONLY permitted while the order is in PLACED state
    if order.status != "PLACED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be cancelled. Current status is '{order.status}' (kitchen preparation already began)."
        )

    # Step 4: Execute state transition and trigger refund
    order.status = "CANCELLED"
    db.commit()
    db.refresh(order)

    # Step 5: Log valid cancellation in Audit Trail
    AuditService.log(
        db=db,
        user_id=current_user.id,
        action="ORDER_CANCELLED",
        entity="ORDER",
        entity_id=order.id,
        status_result="SUCCESS",
        details="Order cancelled by owner prior to staff acceptance; refund triggered."
    )

    return order
```

### 3.4 Security & Architectural Benefit
- **Elimination of BOLA/IDOR**: Direct object references are always scoped against the caller's identity (`order.customer_id == current_user.id`).
- **Finite State Machine Invariant**: Prevents cancellation race conditions once the restaurant accepts or cooks the food.
- **Forensic Auditability**: Unauthorized probing is immediately captured in the security audit ledger.
