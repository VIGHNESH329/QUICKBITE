from typing import List, Tuple, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.models import FoodItem, OrderItem
from app.schemas.schemas import SecureOrderItemInputDTO

class AuthoritativePricingEngine:
    """
    Core Domain Service enforcing Server as Single Source of Truth for financial calculations.
    Completely discards any client-submitted pricing values.
    """
    TAX_RATE: float = 0.10  # 10% tax
    FLAT_DELIVERY_FEE: float = 3.00

    @classmethod
    def calculate_order_totals(
        cls,
        db: Session,
        restaurant_id: int,
        requested_items: List[SecureOrderItemInputDTO]
    ) -> Tuple[List[OrderItem], float, float, float, float]:
        """
        Calculates subtotal, tax, delivery fee, and grand total strictly from canonical DB prices.
        Returns: (order_items_to_persist, subtotal, tax, delivery_fee, grand_total)
        """
        if not requested_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must contain at least one food item."
            )

        item_ids = [item.food_item_id for item in requested_items]
        
        # Query canonical DB items scoped to restaurant and availability
        db_items = db.query(FoodItem).filter(
            FoodItem.id.in_(item_ids),
            FoodItem.restaurant_id == restaurant_id,
            FoodItem.is_available == True
        ).all()

        if len(db_items) != len(set(item_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more selected food items do not exist, are unavailable, or do not belong to this restaurant."
            )

        item_map: Dict[int, FoodItem] = {item.id: item for item in db_items}

        subtotal = 0.0
        order_items_to_persist: List[OrderItem] = []

        for item_input in requested_items:
            canonical_item = item_map[item_input.food_item_id]
            unit_price = round(float(canonical_item.canonical_price), 2)
            qty = item_input.quantity

            if qty < 1 or qty > 99:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid quantity {qty} for item '{canonical_item.name}'. Must be between 1 and 99."
                )

            line_total = round(unit_price * qty, 2)
            subtotal = round(subtotal + line_total, 2)

            order_items_to_persist.append(
                OrderItem(
                    food_item_id=canonical_item.id,
                    snapshot_unit_price=unit_price,
                    quantity=qty
                )
            )

        tax = round(subtotal * cls.TAX_RATE, 2)
        delivery_fee = cls.FLAT_DELIVERY_FEE
        grand_total = round(subtotal + tax + delivery_fee, 2)

        return order_items_to_persist, subtotal, tax, delivery_fee, grand_total
