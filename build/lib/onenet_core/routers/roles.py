from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..schemas import UserRead, RoleCreateRequest
from ..exceptions import APIError
from ..database import get_db
from ..models.user import Role, Permission, User
from ..dependencies import require_permissions

router_roles = APIRouter(prefix="/roles", tags=["roles"])
router_permissions = APIRouter(prefix="/permissions", tags=["permissions"])

@router_roles.get("")
def list_roles(
    user: UserRead = Depends(require_permissions(["role:read"])),
    db: Session = Depends(get_db)
):
    roles = db.query(Role).all()
    roles_data = []
    
    for role in roles:
        user_count = db.query(User).join(User.roles).filter(Role.id == role.id).count()
        
        permissions = [
            {"id": p.id, "name": p.name, "description": p.description}
            for p in role.permissions
        ]

        roles_data.append({
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions": permissions,
            "user_count": user_count,
        })

    return {"success": True, "data": {"roles": roles_data}}


@router_roles.post("", status_code=201)
def create_role(
    payload: RoleCreateRequest,
    user: UserRead = Depends(require_permissions(["role:create"])),
    db: Session = Depends(get_db)
):
    existing = db.query(Role).filter(Role.name == payload.name).first()
    if existing:
        raise APIError(
            status_code=400,
            error_code="PERM-003",
            message=f"Role creation failed: A role with name '{payload.name}' already exists. Please choose a different name.",
        )

    new_role = Role(
        name=payload.name,
        description=payload.description
    )
    
    # Assign permissions
    if payload.permission_names:
        perms = db.query(Permission).filter(Permission.name.in_(payload.permission_names)).all()
        new_role.permissions = perms
    
    db.add(new_role)
    db.commit()
    db.refresh(new_role)

    permissions = [
        {"id": p.id, "name": p.name}
        for p in new_role.permissions
    ]

    return {
        "success": True,
        "data": {
            "id": new_role.id,
            "name": new_role.name,
            "description": new_role.description,
            "permissions": permissions,
        },
        "message": f"Role '{new_role.name}' has been successfully created with {len(permissions)} permission(s).",
    }


@router_permissions.get("")
def list_permissions(
    user: UserRead = Depends(require_permissions(["role:read"])),
    db: Session = Depends(get_db)
):
    perms = db.query(Permission).all()
    return {
        "success": True,
        "data": {
            "permissions": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "category": p.category,
                }
                for p in perms
            ]
        },
    }
