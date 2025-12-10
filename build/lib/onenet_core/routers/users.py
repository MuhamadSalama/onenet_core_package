from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..schemas import (
    UserRead, UserCreateRequest, UserUpdateRequest, AssignRoleRequest
)
from ..exceptions import APIError
from ..database import get_db
from ..models.user import User, Role
from ..utils.security import _now, create_user_read_from_orm
from ..dependencies import require_permissions

router_users = APIRouter(prefix="/users", tags=["users"])

@router_users.get("")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_by: Optional[str] = Query(None, description="Field to sort by (e.g., created_at, name, email)"),
    sort_order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    created_after: Optional[str] = Query(None, description="ISO 8601 date filter"),
    created_before: Optional[str] = Query(None, description="ISO 8601 date filter"),
    user: UserRead = Depends(require_permissions(["user:read"])),
    db: Session = Depends(get_db)
):
    query = db.query(User)

    # Apply filters
    if search:
        search_lower = f"%{search.lower()}%"
        query = query.filter(
            (User.name.ilike(search_lower)) | (User.email.ilike(search_lower))
        )
    
    if role:
        query = query.join(User.roles).filter(Role.name == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    # Date filters
    if created_after:
        try:
            after_date = datetime.fromisoformat(created_after.replace("Z", "+00:00"))
            query = query.filter(User.created_at >= after_date)
        except:
            pass
    
    if created_before:
        try:
            before_date = datetime.fromisoformat(created_before.replace("Z", "+00:00"))
            query = query.filter(User.created_at <= before_date)
        except:
            pass

    # Sorting
    if sort_by:
        reverse_order = sort_order and sort_order.lower() == "desc"
        if sort_by == "created_at":
            query = query.order_by(User.created_at.desc() if reverse_order else User.created_at)
        elif sort_by == "name":
            query = query.order_by(User.name.desc() if reverse_order else User.name)
        elif sort_by == "email":
            query = query.order_by(User.email.desc() if reverse_order else User.email)

    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "success": True,
        "data": {
            "items": [
                {
                    "id": u.id,
                    "email": u.email,
                    "name": u.name,
                    "is_active": u.is_active,
                    "roles": [r.name for r in u.roles],
                    "created_at": u.created_at.isoformat(),
                    "last_login": u.last_login.isoformat() if u.last_login else None,
                }
                for u in users
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
    }


@router_users.get("/{user_id}")
def get_user(
    user_id: int, 
    user: UserRead = Depends(require_permissions(["user:read"])),
    db: Session = Depends(get_db)
):
    found = db.query(User).filter(User.id == user_id).first()
    if not found:
        raise APIError(
            status_code=404,
            error_code="USER-001",
            message=f"User retrieval failed: No user found with ID {user_id}. The user may have been deleted or the ID may be incorrect.",
        )

    role_details = [
        {"id": r.id, "name": r.name, "description": r.description}
        for r in found.roles
    ]
    
    perms = set()
    for r in found.roles:
        for p in r.permissions:
            perms.add(p.name)

    return {
        "success": True,
        "data": {
            "id": found.id,
            "email": found.email,
            "name": found.name,
            "is_active": found.is_active,
            "roles": role_details,
            "permissions": list(perms),
            "created_at": found.created_at.isoformat(),
            "updated_at": found.updated_at.isoformat() if found.updated_at else None,
            "last_login": found.last_login.isoformat() if found.last_login else None,
        },
    }


@router_users.post("", status_code=201)
def create_user(
    payload: UserCreateRequest,
    user: UserRead = Depends(require_permissions(["user:create"])),
    db: Session = Depends(get_db)
):
    if len(payload.password) < 8:
        raise APIError(
            status_code=400,
            error_code="VAL-001",
            message="User creation failed: Password must be at least 8 characters long.",
        )

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise APIError(
            status_code=400,
            error_code="USER-002",
            message=f"User creation failed: A user with email '{payload.email}' already exists. Please use a different email address.",
        )

    new_user = User(
        email=payload.email,
        name=payload.name,
        password_hash=payload.password,
        is_active=payload.is_active,
        created_at=_now(),
    )
    
    # Assign roles
    if payload.roles:
        roles = db.query(Role).filter(Role.name.in_(payload.roles)).all()
        new_user.roles = roles
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "success": True,
        "data": {
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "is_active": new_user.is_active,
            "roles": [r.name for r in new_user.roles],
            "created_at": new_user.created_at.isoformat(),
        },
        "message": f"User '{new_user.name}' (ID: {new_user.id}) has been successfully created with email '{new_user.email}'.",
    }


@router_users.put("/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    current_user: UserRead = Depends(require_permissions(["user:update"])),
    db: Session = Depends(get_db)
):
    found = db.query(User).filter(User.id == user_id).first()
    if not found:
        raise APIError(
            status_code=404,
            error_code="USER-001",
            message=f"User update failed: No user found with ID {user_id}. The user may have been deleted or the ID may be incorrect.",
        )

    if payload.name is not None:
        found.name = payload.name
    
    if payload.email is not None:
        other = db.query(User).filter(User.email == payload.email, User.id != user_id).first()
        if other:
            raise APIError(
                status_code=400,
                error_code="USER-002",
                message="User with this email already exists",
            )
        found.email = payload.email
    
    if payload.is_active is not None:
        found.is_active = payload.is_active
    
    if payload.roles is not None:
        roles = db.query(Role).filter(Role.name.in_(payload.roles)).all()
        found.roles = roles

    found.updated_at = _now()
    db.commit()
    db.refresh(found)

    return {
        "success": True,
        "data": {
            "id": found.id,
            "email": found.email,
            "name": found.name,
            "is_active": found.is_active,
            "roles": [r.name for r in found.roles],
            "updated_at": found.updated_at.isoformat(),
        },
        "message": f"User '{found.name}' (ID: {user_id}) has been successfully updated.",
    }


@router_users.delete("/{user_id}")
def deactivate_user(
    user_id: int,
    current_user: UserRead = Depends(require_permissions(["user:delete"])),
    db: Session = Depends(get_db)
):
    if user_id == current_user.id:
        raise APIError(
            status_code=403,
            error_code="USER-004",
            message="User deactivation failed: You cannot deactivate your own account. Please ask another administrator to perform this action.",
        )

    found = db.query(User).filter(User.id == user_id).first()
    if not found:
        raise APIError(
            status_code=404,
            error_code="USER-001",
            message=f"User deactivation failed: No user found with ID {user_id}. The user may have already been deleted.",
        )

    found.is_active = False
    found.updated_at = _now()
    db.commit()

    return {
        "success": True,
        "message": f"User '{found.name}' (ID: {user_id}) has been successfully deactivated. The user will no longer be able to access the system.",
    }


@router_users.get("/{user_id}/roles")
def get_user_roles(
    user_id: int, 
    user: UserRead = Depends(require_permissions(["user:read"])),
    db: Session = Depends(get_db)
):
    found = db.query(User).filter(User.id == user_id).first()
    if not found:
        raise APIError(
            status_code=404,
            error_code="USER-001",
            message=f"Failed to retrieve user roles: No user found with ID {user_id}.",
        )

    roles = [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "assigned_at": found.created_at.isoformat(),
        }
        for r in found.roles
    ]

    return {"success": True, "data": {"user_id": user_id, "roles": roles}}


@router_users.post("/{user_id}/roles")
def assign_role_to_user(
    user_id: int,
    payload: AssignRoleRequest,
    user: UserRead = Depends(require_permissions(["user:update", "role:assign"])),
    db: Session = Depends(get_db)
):
    found = db.query(User).filter(User.id == user_id).first()
    if not found:
        raise APIError(
            status_code=404,
            error_code="USER-001",
            message=f"Failed to assign role: No user found with ID {user_id}.",
        )

    role = db.query(Role).filter(Role.name == payload.role_name).first()
    if not role:
        all_roles = db.query(Role).all()
        raise APIError(
            status_code=404,
            error_code="PERM-003",
            message=f"Failed to assign role: Role '{payload.role_name}' does not exist. Available roles: {', '.join([r.name for r in all_roles])}.",
        )

    if role not in found.roles:
        found.roles.append(role)
        found.updated_at = _now()
        db.commit()

    return {
        "success": True,
        "message": f"Role '{payload.role_name}' has been successfully assigned to user '{found.name}' (ID: {user_id}).",
    }


@router_users.delete("/{user_id}/roles/{role_name}")
def remove_role_from_user(
    user_id: int,
    role_name: str,
    user: UserRead = Depends(require_permissions(["user:update", "role:assign"])),
    db: Session = Depends(get_db)
):
    found = db.query(User).filter(User.id == user_id).first()
    if not found:
        raise APIError(
            status_code=404,
            error_code="USER-001",
            message=f"Failed to remove role: No user found with ID {user_id}.",
        )

    role = db.query(Role).filter(Role.name == role_name).first()
    if role and role in found.roles:
        found.roles.remove(role)
        found.updated_at = _now()
        db.commit()

    return {
        "success": True,
        "message": f"Role '{role_name}' has been successfully removed from user '{found.name}' (ID: {user_id}).",
    }
