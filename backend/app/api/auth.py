from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.rate_limit import login_rate_limiter
from app.models.models import User
from app.schemas.schemas import UserRegisterDTO, UserLoginDTO, TokenResponseDTO, UserResponseDTO
from app.services.audit import AuditService
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserRegisterDTO,
    request: Request,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"

    # Check for existing email to prevent duplicate accounts
    existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Hash password with bcrypt
    hashed_pw = hash_password(payload.password)

    new_user = User(
        email=payload.email.lower(),
        password_hash=hashed_pw,
        full_name=payload.full_name,
        role=payload.role,
        restaurant_id=payload.restaurant_id,
        phone=payload.phone
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    AuditService.log(
        db=db,
        user_id=new_user.id,
        action_type="AUTH_REGISTER_SUCCESS",
        entity_name="USER",
        entity_id=new_user.id,
        client_ip=client_ip,
        details_json=f"Registered role={new_user.role}"
    )

    return new_user

@router.post("/login", response_model=TokenResponseDTO)
def login_user(
    payload: UserLoginDTO,
    request: Request,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"

    # Rate limiting enforcement
    login_rate_limiter.check(client_ip)

    user = db.query(User).filter(User.email == payload.email.lower()).first()
    
    # Secure constant-time password check
    if not user or not verify_password(payload.password, user.password_hash):
        AuditService.log(
            db=db,
            user_id=user.id if user else None,
            action_type="AUTH_LOGIN_FAILURE",
            entity_name="USER",
            status_result="FAILURE",
            client_ip=client_ip,
            details_json=f"Failed login attempt for email: {payload.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue signed JWT with subject, role, and restaurant_id
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "restaurant_id": user.restaurant_id
    }
    token = create_access_token(data=token_data)

    AuditService.log(
        db=db,
        user_id=user.id,
        action_type="AUTH_LOGIN_SUCCESS",
        entity_name="USER",
        entity_id=user.id,
        client_ip=client_ip,
        details_json=f"Logged in with role: {user.role}"
    )

    return {
        "access_token": token,
        "token_type": "bearer",  # nosec: B105
        "user": user
    }

@router.get("/me", response_model=UserResponseDTO)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user
