from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Order, OrderItem, Restaurant, Payment, User, Cart, CartItem
from app.schemas.schemas import (
    SecureOrderCreateDTO,
    OrderResponseDTO,
    OrderDetailDTO,
    OrderItemDetailDTO,
    OrderStatusUpdateDTO
)
from app.api.deps import get_current_user, require_customer, require_staff
from app.services.pricing import AuthoritativePricingEngine
from app.services.payment import TokenizedPaymentGatewayAdapter
from app.services.audit import AuditService

router = APIRouter(prefix="/orders", tags=["Orders"])

# Valid state machine transitions
ALLOWED_TRANSITIONS = {
    "PLACED": ["ACCEPTED", "REJECTED", "CANCELLED"],
    "ACCEPTED": ["PREPARING"],
    "PREPARING": ["OUT_FOR_DELIVERY"],
    "OUT_FOR_DELIVERY": ["DELIVERED"],
    "DELIVERED": [],
    "REJECTED": [],
    "CANCELLED": []
}

@router.post("", response_model=OrderResponseDTO, status_code=status.HTTP_201_CREATED)
def place_order(
    payload: SecureOrderCreateDTO,
    request: Request,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"

    # Step 1: Verify Restaurant is active
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == payload.restaurant_id,
        Restaurant.is_active == True
    ).first()
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected restaurant is inactive or does not exist."
        )

    # Step 2: Authoritative Server Pricing (Discards any client price)
    order_items, subtotal, tax, delivery_fee, grand_total = AuthoritativePricingEngine.calculate_order_totals(
        db=db,
        restaurant_id=payload.restaurant_id,
        requested_items=payload.items
    )

    # Step 3: Process tokenized charge via payment gateway adapter
    payment_result = TokenizedPaymentGatewayAdapter.process_charge(
        token=payload.payment_token,
        amount=grand_total,
        customer_email=current_user.email
    )

    if not payment_result.success:
        AuditService.log(
            db=db,
            user_id=current_user.id,
            action_type="PAYMENT_FAILED",
            entity_name="ORDER",
            status_result="FAILURE",
            client_ip=client_ip,
            details_json=f"Payment declined: {payment_result.message}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment processing failed: {payment_result.message}"
        )

    # Step 4: Atomic order creation
    new_order = Order(
        customer_id=current_user.id,
        restaurant_id=payload.restaurant_id,
        subtotal_amount=subtotal,
        tax_amount=tax,
        delivery_fee=delivery_fee,
        total_amount=grand_total,
        delivery_address=payload.delivery_address,
        status="PLACED"
    )
    db.add(new_order)
    db.flush()  # Assigns new_order.id

    for item in order_items:
        item.order_id = new_order.id
        db.add(item)

    payment_record = Payment(
        order_id=new_order.id,
        transaction_reference=payment_result.transaction_reference,
        amount=grand_total,
        payment_status="SUCCESS",
        payment_token_masked=payment_result.masked_token
    )
    db.add(payment_record)

    # Clear customer's cart
    user_cart = db.query(Cart).filter(Cart.customer_id == current_user.id).first()
    if user_cart:
        db.query(CartItem).filter(CartItem.cart_id == user_cart.id).delete()

    db.commit()
    db.refresh(new_order)

    # Step 5: Audit Log
    AuditService.log(
        db=db,
        user_id=current_user.id,
        action_type="ORDER_CREATED",
        entity_name="ORDER",
        entity_id=new_order.id,
        client_ip=client_ip,
        details_json=f"Order placed with authoritative amount: ${grand_total}. TxRef: {payment_result.transaction_reference}"
    )

    return new_order

@router.get("", response_model=List[OrderDetailDTO])
def get_my_orders(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """Returns only orders belonging to the authenticated customer."""
    orders = db.query(Order).filter(Order.customer_id == current_user.id).order_by(Order.created_at.desc()).all()
    results = []
    for o in orders:
        items_dto = [
            OrderItemDetailDTO(
                id=i.id,
                food_item_id=i.food_item_id,
                food_item_name=i.food_item.name if i.food_item else "Unknown Item",
                snapshot_unit_price=i.snapshot_unit_price,
                quantity=i.quantity,
                line_total=round(i.snapshot_unit_price * i.quantity, 2)
            ) for i in o.items
        ]
        results.append(
            OrderDetailDTO(
                id=o.id,
                customer_id=o.customer_id,
                restaurant_id=o.restaurant_id,
                subtotal_amount=o.subtotal_amount,
                tax_amount=o.tax_amount,
                delivery_fee=o.delivery_fee,
                total_amount=o.total_amount,
                status=o.status,
                delivery_address=o.delivery_address,
                created_at=o.created_at,
                updated_at=o.updated_at,
                restaurant_name=o.restaurant.name if o.restaurant else None,
                customer_name=o.customer.full_name if o.customer else None,
                items=items_dto
            )
        )
    return results

@router.get("/kitchen", response_model=List[OrderDetailDTO])
def get_kitchen_orders(
    current_staff: User = Depends(require_staff),
    db: Session = Depends(get_db)
):
    """Returns incoming orders scoped strictly to staff's assigned restaurant."""
    if current_staff.role != "admin" and not current_staff.restaurant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Staff account is not assigned to any restaurant.")

    query = db.query(Order)
    if current_staff.role != "admin":
        query = query.filter(Order.restaurant_id == current_staff.restaurant_id)

    orders = query.order_by(Order.created_at.desc()).all()
    results = []
    for o in orders:
        items_dto = [
            OrderItemDetailDTO(
                id=i.id,
                food_item_id=i.food_item_id,
                food_item_name=i.food_item.name if i.food_item else "Unknown Item",
                snapshot_unit_price=i.snapshot_unit_price,
                quantity=i.quantity,
                line_total=round(i.snapshot_unit_price * i.quantity, 2)
            ) for i in o.items
        ]
        results.append(
            OrderDetailDTO(
                id=o.id,
                customer_id=o.customer_id,
                restaurant_id=o.restaurant_id,
                subtotal_amount=o.subtotal_amount,
                tax_amount=o.tax_amount,
                delivery_fee=o.delivery_fee,
                total_amount=o.total_amount,
                status=o.status,
                delivery_address=o.delivery_address,
                created_at=o.created_at,
                updated_at=o.updated_at,
                restaurant_name=o.restaurant.name if o.restaurant else None,
                customer_name=o.customer.full_name if o.customer else None,
                items=items_dto
            )
        )
    return results

@router.get("/{order_id}", response_model=OrderDetailDTO)
def get_order_by_id(
    order_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enforces BOLA/IDOR ownership protection."""
    client_ip = request.client.host if request.client else "unknown"
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    # Authorization Check:
    # 1. Admin has global visibility
    # 2. Customer can only view own order
    # 3. Staff can only view order belonging to their assigned restaurant
    is_authorized = False
    if current_user.role == "admin":
        is_authorized = True
    elif current_user.role == "customer" and order.customer_id == current_user.id:
        is_authorized = True
    elif current_user.role == "restaurant_staff" and order.restaurant_id == current_user.restaurant_id:
        is_authorized = True

    if not is_authorized:
        AuditService.log(
            db=db,
            user_id=current_user.id,
            action_type="AUTHZ_FAILURE_ORDER_MISMATCH",
            entity_name="ORDER",
            entity_id=order_id,
            status_result="FAILURE",
            client_ip=client_ip,
            details_json=f"User {current_user.id} ({current_user.role}) attempted unauthorized access to Order {order_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to view this order."
        )

    items_dto = [
        OrderItemDetailDTO(
            id=i.id,
            food_item_id=i.food_item_id,
            food_item_name=i.food_item.name if i.food_item else "Unknown Item",
            snapshot_unit_price=i.snapshot_unit_price,
            quantity=i.quantity,
            line_total=round(i.snapshot_unit_price * i.quantity, 2)
        ) for i in order.items
    ]

    return OrderDetailDTO(
        id=order.id,
        customer_id=order.customer_id,
        restaurant_id=order.restaurant_id,
        subtotal_amount=order.subtotal_amount,
        tax_amount=order.tax_amount,
        delivery_fee=order.delivery_fee,
        total_amount=order.total_amount,
        status=order.status,
        delivery_address=order.delivery_address,
        created_at=order.created_at,
        updated_at=order.updated_at,
        restaurant_name=order.restaurant.name if order.restaurant else None,
        customer_name=order.customer.full_name if order.customer else None,
        items=items_dto
    )

@router.post("/{order_id}/cancel", response_model=OrderResponseDTO)
def cancel_order(
    order_id: int,
    request: Request,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """Customer-initiated cancellation with ownership and state invariant checks."""
    client_ip = request.client.host if request.client else "unknown"
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    # Ownership check
    if order.customer_id != current_user.id and current_user.role != "admin":
        AuditService.log(
            db=db,
            user_id=current_user.id,
            action_type="AUTHZ_FAILURE_CANCEL_MISMATCH",
            entity_name="ORDER",
            entity_id=order_id,
            status_result="FAILURE",
            client_ip=client_ip,
            details_json=f"User {current_user.id} tried cancelling Order {order_id} owned by {order.customer_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only cancel your own orders."
        )

    # State Machine check: Only allowed while PLACED
    if order.status != "PLACED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be cancelled. Current status is '{order.status}'. Cancellation is only allowed before restaurant accepts."
        )

    order.status = "CANCELLED"
    db.commit()
    db.refresh(order)

    AuditService.log(
        db=db,
        user_id=current_user.id,
        action_type="ORDER_CANCELLED",
        entity_name="ORDER",
        entity_id=order.id,
        client_ip=client_ip,
        details_json="Customer cancelled order prior to staff acceptance. Refund initiated."
    )

    return order

@router.patch("/{order_id}/status", response_model=OrderResponseDTO)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdateDTO,
    request: Request,
    current_staff: User = Depends(require_staff),
    db: Session = Depends(get_db)
):
    """Restaurant staff updates order status with tenant and FSM validation."""
    client_ip = request.client.host if request.client else "unknown"
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    # Multi-tenant scoping check
    if current_staff.role != "admin" and order.restaurant_id != current_staff.restaurant_id:
        AuditService.log(
            db=db,
            user_id=current_staff.id,
            action_type="AUTHZ_FAILURE_STAFF_TENANT",
            entity_name="ORDER",
            entity_id=order_id,
            status_result="FAILURE",
            client_ip=client_ip,
            details_json=f"Staff from rest_id={current_staff.restaurant_id} attempted status change on Order {order_id} (rest_id={order.restaurant_id})"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only manage orders for your assigned restaurant."
        )

    # Finite State Machine check
    allowed_next = ALLOWED_TRANSITIONS.get(order.status, [])
    if payload.status not in allowed_next:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Illegal state transition from '{order.status}' to '{payload.status}'. Allowed transitions: {allowed_next}"
        )

    old_status = order.status
    order.status = payload.status
    db.commit()
    db.refresh(order)

    AuditService.log(
        db=db,
        user_id=current_staff.id,
        action_type="ORDER_STATUS_CHANGED",
        entity_name="ORDER",
        entity_id=order.id,
        client_ip=client_ip,
        details_json=f"Order {order.id} status transitioned from '{old_status}' to '{order.status}'"
    )

    return order
