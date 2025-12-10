from fastapi import APIRouter, Response, Request, Depends, Cookie
from typing import Optional
from sqlalchemy.orm import Session
from ..schemas import (
    RegisterResponse, RegisterRequest, LoginResponse, LoginRequest, LogoutResponse,
    UserRead, ChangePasswordResponse, ChangePasswordRequest
)
from ..exceptions import APIError
from ..database import get_db
from ..models.user import User
from ..utils.security import (
    _now, create_session_for_user, delete_session_from_db, create_user_read_from_orm
)
from ..dependencies import get_current_user
from ..config import SESSION_TTL_SECONDS

router_auth = APIRouter(prefix="/auth", tags=["auth"])

@router_auth.post("/register", response_model=RegisterResponse)
def register(
    payload: RegisterRequest, 
    response: Response, 
    request: Request,
    db: Session = Depends(get_db)
):
    # Validate password strength
    if len(payload.password) < 8:
        raise APIError(
            status_code=400,
            error_code="VAL-001",
            message="Password must be at least 8 characters long",
        )

    # Check if user already exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise APIError(
            status_code=400,
            error_code="USER-002",
            message=f"Registration failed: A user with email '{payload.email}' already exists. Please use a different email or try logging in.",
        )

    # Get default user role
    from ..models.user import Role
    user_role = db.query(Role).filter(Role.name == "user").first()
    
    new_user = User(
        email=payload.email,
        name=payload.name,
        password_hash=payload.password,  # Note: In production, hash this!
        is_active=True,
        created_at=_now(),
        last_login=_now()
    )
    
    if user_role:
        new_user.roles.append(user_role)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create session
    session_id = create_session_for_user(db, new_user)

    # Set HTTP-only cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )

    user_dto = create_user_read_from_orm(new_user)
    
    return RegisterResponse(
        success=True,
        data={
            "user": {
                "id": user_dto.id,
                "email": user_dto.email,
                "name": user_dto.name,
                "is_active": user_dto.is_active,
                "roles": user_dto.roles,
                "created_at": user_dto.created_at.isoformat(),
            },
            "session_id": session_id,
        },
        message=f"Registration successful! Welcome, {new_user.name}. Your account has been created and you are now logged in.",
    )


@router_auth.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest, 
    response: Response, 
    request: Request,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise APIError(
            status_code=401,
            error_code="AUTH-001",
            message=f"Login failed: No account found with email '{payload.email}'. Please check your email or register a new account.",
        )
    
    if user.password_hash != payload.password:
        raise APIError(
            status_code=401,
            error_code="AUTH-001",
            message="Login failed: The password you entered is incorrect. Please try again or reset your password.",
        )

    # Update last_login
    user.last_login = _now()
    db.commit()

    session_id = create_session_for_user(db, user)

    # Set HTTP-only cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )

    user_dto = create_user_read_from_orm(user)

    return LoginResponse(
        success=True,
        data={
            "user": {
                "id": user_dto.id,
                "email": user_dto.email,
                "name": user_dto.name,
                "is_active": user_dto.is_active,
                "roles": user_dto.roles,
                "created_at": user_dto.created_at.isoformat(),
            },
            "session_id": session_id,
        },
        message=f"Login successful! Welcome back, {user.name}.",
    )


@router_auth.post("/logout", response_model=LogoutResponse)
def logout(
    response: Response,
    user: UserRead = Depends(get_current_user),
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    delete_session_from_db(db, session_id)
    response.delete_cookie(key="session_id", path="/")
    return LogoutResponse(
        success=True,
        message=f"Logged out successfully. Goodbye, {user.name}! Your session has been terminated.",
    )


@router_auth.get("/me")
def get_current_user_profile(user: UserRead = Depends(get_current_user)):
    return {
        "success": True,
        "data": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_active": user.is_active,
            "roles": user.roles,
            "permissions": user.permissions,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
        },
    }


@router_auth.post("/change-password", response_model=ChangePasswordResponse)
def change_password(
    payload: ChangePasswordRequest, 
    user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.id == user.id).first()
    if not db_user:
        raise APIError(
            status_code=404,
            error_code="USER-001",
            message="User account not found. Please log in again.",
        )

    if db_user.password_hash != payload.current_password:
        raise APIError(
            status_code=400,
            error_code="AUTH-006",
            message="Password change failed: The current password you entered is incorrect. Please verify your current password and try again.",
        )

    if len(payload.new_password) < 8:
        raise APIError(
            status_code=400,
            error_code="VAL-001",
            message="Password change failed: New password must be at least 8 characters long.",
        )

    db_user.password_hash = payload.new_password
    db.commit()

    return ChangePasswordResponse(
        success=True,
        message=f"Password successfully changed for account {user.email}. Please use your new password for future logins.",
    )
