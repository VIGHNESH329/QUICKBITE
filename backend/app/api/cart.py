from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Cart, CartItem, FoodItem, User
from app.schemas.schemas import CartResponseDTO, CartItemDTO, CartItemInputDTO
from app.api.deps import require_customer

router = APIRouter(prefix="/cart", tags=["Cart"])

def _get_or_create_cart(db: Session, customer_id: int) -> Cart:
    cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
    if not cart:
        cart = Cart(customer_id=customer_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

@router.get("", response_model=CartResponseDTO)
def get_cart(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    cart = _get_or_create_cart(db, current_user.id)
    items_dto = []
    subtotal = 0.0

    for ci in cart.items:
        if ci.food_item:
            line = round(ci.food_item.canonical_price * ci.quantity, 2)
            subtotal = round(subtotal + line, 2)
            items_dto.append(
                CartItemDTO(
                    id=ci.id,
                    food_item_id=ci.food_item_id,
                    food_item_name=ci.food_item.name,
                    unit_price=ci.food_item.canonical_price,
                    quantity=ci.quantity,
                    line_total=line
                )
            )

    return CartResponseDTO(
        id=cart.id,
        items=items_dto,
        subtotal=subtotal
    )

@router.post("", response_model=CartResponseDTO)
def update_cart_item(
    payload: CartItemInputDTO,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    food_item = db.query(FoodItem).filter(FoodItem.id == payload.food_item_id, FoodItem.is_available == True).first()
    if not food_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food item not found or currently unavailable.")

    cart = _get_or_create_cart(db, current_user.id)
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.food_item_id == payload.food_item_id
    ).first()

    if existing_item:
        existing_item.quantity = payload.quantity
    else:
        new_item = CartItem(
            cart_id=cart.id,
            food_item_id=payload.food_item_id,
            quantity=payload.quantity
        )
        db.add(new_item)

    db.commit()
    return get_cart(current_user=current_user, db=db)

@router.delete("/items/{food_item_id}", response_model=CartResponseDTO)
def remove_from_cart(
    food_item_id: int,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    cart = _get_or_create_cart(db, current_user.id)
    item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.food_item_id == food_item_id
    ).first()
    if item:
        db.delete(item)
        db.commit()
    return get_cart(current_user=current_user, db=db)

@router.delete("", response_model=CartResponseDTO)
def clear_cart(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    cart = _get_or_create_cart(db, current_user.id)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    return CartResponseDTO(id=cart.id, items=[], subtotal=0.0)
