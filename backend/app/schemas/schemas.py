from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime

# --- Authentication Schemas ---

class UserRegisterDTO(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100, description="Password min 8 chars")
    full_name: str = Field(..., min_length=2, max_length=100)
    role: str = Field("customer", description="Public registration is restricted to customer")
    restaurant_id: Optional[int] = None
    phone: Optional[str] = Field(None, max_length=20)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit.")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v.lower() != "customer":
            raise ValueError("Public self-registration is strictly restricted to the 'customer' role. Staff/Admin accounts are provisioned administratively.")
        return "customer"


class UserLoginDTO(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=100)


class UserResponseDTO(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    restaurant_id: Optional[int] = None
    phone: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponseDTO(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponseDTO


# --- Restaurant & Food Schemas ---

class FoodItemDTO(BaseModel):
    id: int
    restaurant_id: int
    name: str
    description: Optional[str] = None
    canonical_price: float
    category: str
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class FoodItemCreateDTO(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    canonical_price: float = Field(..., ge=0.01, le=1000.0, description="Price must be positive")
    category: str = Field("General", min_length=2, max_length=50)
    is_available: bool = True


class FoodItemUpdateDTO(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    canonical_price: Optional[float] = Field(None, ge=0.01, le=1000.0)
    category: Optional[str] = Field(None, min_length=2, max_length=50)
    is_available: Optional[bool] = None


class RestaurantDTO(BaseModel):
    id: int
    name: str
    cuisine_type: str
    address: str
    phone: Optional[str] = None
    is_active: bool
    food_items: List[FoodItemDTO] = []

    model_config = ConfigDict(from_attributes=True)


# --- Cart Schemas ---

class CartItemInputDTO(BaseModel):
    food_item_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=99, description="Quantity must be between 1 and 99")


class CartItemDTO(BaseModel):
    id: int
    food_item_id: int
    food_item_name: str
    unit_price: float
    quantity: int
    line_total: float


class CartResponseDTO(BaseModel):
    id: int
    items: List[CartItemDTO] = []
    subtotal: float = 0.0


# --- Order Schemas ---

class SecureOrderItemInputDTO(BaseModel):
    food_item_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=99)
    # SECURITY NOTE: No unit_price or line_total accepted here!


class SecureOrderCreateDTO(BaseModel):
    restaurant_id: int = Field(..., gt=0)
    items: List[SecureOrderItemInputDTO] = Field(..., min_length=1, max_length=50)
    delivery_address: str = Field(..., min_length=5, max_length=250)
    payment_token: str = Field(..., min_length=5, max_length=100)
    # SECURITY NOTE: No total_amount or price parameters accepted!


class OrderItemDetailDTO(BaseModel):
    id: int
    food_item_id: int
    food_item_name: str
    snapshot_unit_price: float
    quantity: int
    line_total: float

    model_config = ConfigDict(from_attributes=True)


class OrderResponseDTO(BaseModel):
    id: int
    customer_id: int
    restaurant_id: int
    subtotal_amount: float
    tax_amount: float
    delivery_fee: float
    total_amount: float
    status: str
    delivery_address: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderDetailDTO(OrderResponseDTO):
    items: List[OrderItemDetailDTO] = []
    restaurant_name: Optional[str] = None
    customer_name: Optional[str] = None


class OrderStatusUpdateDTO(BaseModel):
    status: str = Field(..., description="Target status in lifecycle")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = ["ACCEPTED", "REJECTED", "PREPARING", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"]
        if v not in valid_statuses:
            raise ValueError(f"Invalid order status transition. Allowed: {valid_statuses}")
        return v


# --- Audit Log Schema ---

class AuditLogDTO(BaseModel):
    id: int
    user_id: Optional[int] = None
    action_type: str
    entity_name: str
    entity_id: Optional[int] = None
    status_result: str
    client_ip: Optional[str] = None
    details_json: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
