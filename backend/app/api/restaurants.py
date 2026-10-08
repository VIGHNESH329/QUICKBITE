from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Restaurant, FoodItem, User
from app.schemas.schemas import RestaurantDTO, FoodItemDTO, FoodItemCreateDTO, FoodItemUpdateDTO
from app.api.deps import get_current_user, require_staff
from app.services.audit import AuditService

router = APIRouter(prefix="/restaurants", tags=["Restaurants & Menus"])

@router.get("", response_model=List[RestaurantDTO])
def list_restaurants(db: Session = Depends(get_db)):
    """Returns active restaurants along with their available menu offerings."""
    restaurants = db.query(Restaurant).filter(Restaurant.is_active == True).all()
    return restaurants

@router.get("/{restaurant_id}", response_model=RestaurantDTO)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id, Restaurant.is_active == True).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found or currently inactive.")
    return restaurant

@router.get("/{restaurant_id}/menu", response_model=List[FoodItemDTO])
def get_restaurant_menu(restaurant_id: int, db: Session = Depends(get_db)):
    items = db.query(FoodItem).filter(
        FoodItem.restaurant_id == restaurant_id,
        FoodItem.is_available == True
    ).all()
    return items

@router.post("/{restaurant_id}/menu", response_model=FoodItemDTO, status_code=status.HTTP_201_CREATED)
def create_food_item(
    restaurant_id: int,
    payload: FoodItemCreateDTO,
    request: Request,
    current_staff: User = Depends(require_staff),
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"

    # Multi-tenant authorization check
    if current_staff.role != "admin" and current_staff.restaurant_id != restaurant_id:
        AuditService.log(
            db=db,
            user_id=current_staff.id,
            action_type="AUTHZ_FAILURE_MENU_MODIFICATION",
            entity_name="RESTAURANT",
            entity_id=restaurant_id,
            status_result="FAILURE",
            client_ip=client_ip,
            details_json=f"Staff from rest_id={current_staff.restaurant_id} tried modifying rest_id={restaurant_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only manage menu items for your assigned restaurant."
        )

    new_item = FoodItem(
        restaurant_id=restaurant_id,
        name=payload.name,
        description=payload.description,
        canonical_price=round(payload.canonical_price, 2),
        category=payload.category,
        is_available=payload.is_available
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    AuditService.log(
        db=db,
        user_id=current_staff.id,
        action_type="MENU_ITEM_CREATED",
        entity_name="FOOD_ITEM",
        entity_id=new_item.id,
        client_ip=client_ip,
        details_json=f"Created '{new_item.name}' at price ${new_item.canonical_price}"
    )

    return new_item

@router.patch("/{restaurant_id}/menu/{item_id}", response_model=FoodItemDTO)
def update_food_item(
    restaurant_id: int,
    item_id: int,
    payload: FoodItemUpdateDTO,
    request: Request,
    current_staff: User = Depends(require_staff),
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"

    if current_staff.role != "admin" and current_staff.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only update menu items for your assigned restaurant."
        )

    item = db.query(FoodItem).filter(FoodItem.id == item_id, FoodItem.restaurant_id == restaurant_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found in this restaurant.")

    if payload.name is not None:
        item.name = payload.name
    if payload.description is not None:
        item.description = payload.description
    if payload.canonical_price is not None:
        old_price = item.canonical_price
        item.canonical_price = round(payload.canonical_price, 2)
        AuditService.log(
            db=db,
            user_id=current_staff.id,
            action_type="MENU_PRICE_CHANGED",
            entity_name="FOOD_ITEM",
            entity_id=item.id,
            client_ip=client_ip,
            details_json=f"Price revised from ${old_price} to ${item.canonical_price}"
        )
    if payload.category is not None:
        item.category = payload.category
    if payload.is_available is not None:
        item.is_available = payload.is_available

    db.commit()
    db.refresh(item)
    return item
