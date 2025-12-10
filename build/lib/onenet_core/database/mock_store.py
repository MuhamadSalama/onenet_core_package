from typing import Dict, Any, List
from datetime import datetime, timedelta
from ..models.schemas import UserProfile, Role, Permission, SessionRecord

# Demo users with emails instead of usernames
DEMO_USERS: Dict[str, Dict[str, Any]] = {
    "demo@example.com": {
        "password": "demo123",
        "profile": UserProfile(
            id=1,
            email="demo@example.com",
            name="Demo User",
            is_active=True,
            roles=["user"],
            permissions=["user:read", "wallet:read", "wallet:transfer"],
            created_at=datetime.utcnow() - timedelta(days=30),
        ),
    },
    "admin@example.com": {
        "password": "admin123",
        "profile": UserProfile(
            id=2,
            email="admin@example.com",
            name="Admin User",
            is_active=True,
            roles=["admin", "manager"],
            permissions=[
                "user:read",
                "user:create",
                "user:update",
                "user:delete",
                "wallet:read",
                "wallet:transfer",
                "role:read",
                "role:create",
                "role:assign",
                "admin:panel",
                "risk:console",
            ],
            created_at=datetime.utcnow() - timedelta(days=60),
        ),
    },
}

# Demo roles
DEMO_ROLES: Dict[str, Role] = {
    "admin": Role(id=1, name="admin", description="Administrator with full access"),
    "manager": Role(
        id=2, name="manager", description="Manager with elevated permissions"
    ),
    "user": Role(id=3, name="user", description="Standard user role"),
}

# Demo permissions
DEMO_PERMISSIONS: List[Permission] = [
    Permission(
        id=1,
        name="user:create",
        description="Create new users",
        category="user_management",
    ),
    Permission(
        id=2,
        name="user:read",
        description="View user information",
        category="user_management",
    ),
    Permission(
        id=3, name="user:update", description="Update users", category="user_management"
    ),
    Permission(
        id=4, name="user:delete", description="Delete users", category="user_management"
    ),
    Permission(
        id=5,
        name="wallet:read",
        description="View wallet information",
        category="wallet",
    ),
    Permission(
        id=6,
        name="wallet:transfer",
        description="Perform wallet transfers",
        category="wallet",
    ),
    Permission(
        id=7, name="role:read", description="View roles", category="role_management"
    ),
    Permission(
        id=8, name="role:create", description="Create roles", category="role_management"
    ),
    Permission(
        id=9,
        name="role:assign",
        description="Assign roles to users",
        category="role_management",
    ),
]

SESSIONS: Dict[str, SessionRecord] = {}

# Demo user storage for user management endpoints
USER_STORE: Dict[int, UserProfile] = {
    user["profile"].id: user["profile"] for user in DEMO_USERS.values()
}
_next_user_id = max([u["profile"].id for u in DEMO_USERS.values()], default=0) + 1
