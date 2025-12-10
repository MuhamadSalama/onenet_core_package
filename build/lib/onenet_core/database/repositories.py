from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta
from uuid import uuid4
from ..models.schemas import UserProfile, Role, Permission, SessionRecord
from .mock_store import USER_STORE, DEMO_USERS, DEMO_ROLES, DEMO_PERMISSIONS, SESSIONS, _next_user_id
from ..config import SESSION_TTL_SECONDS

class BaseRepository:
    pass

class UserRepository(BaseRepository):
    def get(self, user_id: int) -> Optional[UserProfile]:
        return USER_STORE.get(user_id)

    def get_by_email(self, email: str) -> Optional[UserProfile]:
        if email in DEMO_USERS:
            return DEMO_USERS[email]["profile"]
        for u in USER_STORE.values():
            if u.email == email:
                return u
        return None

    def get_all(self) -> List[UserProfile]:
        return list(USER_STORE.values())

    def create(self, user: UserProfile, password: str = None) -> UserProfile:
        USER_STORE[user.id] = user
        if password:
            DEMO_USERS[user.email] = {"password": password, "profile": user}
        else:
             if user.email not in DEMO_USERS:
                 DEMO_USERS[user.email] = {"password": "default_password", "profile": user}
        return user

    def update(self, user: UserProfile) -> UserProfile:
        USER_STORE[user.id] = user
        if user.email in DEMO_USERS:
            DEMO_USERS[user.email]["profile"] = user
        return user

    def delete(self, user_id: int):
        pass

    def next_id(self) -> int:
        return max([u.id for u in USER_STORE.values()], default=0) + 1

    def authenticate(self, email: str, password: str) -> Optional[UserProfile]:
        entry = DEMO_USERS.get(email)
        if not entry:
            return None
        if entry["password"] == password:
            return entry["profile"]
        return None

    def change_password(self, email: str, new_password: str):
        if email in DEMO_USERS:
            DEMO_USERS[email]["password"] = new_password
    
    def verify_password(self, email: str, password: str) -> bool:
        entry = DEMO_USERS.get(email)
        if not entry:
            return False
        return entry["password"] == password


class RoleRepository(BaseRepository):
    def get(self, role_name: str) -> Optional[Role]:
        return DEMO_ROLES.get(role_name)

    def get_all(self) -> List[Role]:
        return list(DEMO_ROLES.values())
    
    def create(self, role: Role) -> Role:
        DEMO_ROLES[role.name] = role
        return role
    
    def exists(self, role_name: str) -> bool:
        return role_name in DEMO_ROLES


class PermissionRepository(BaseRepository):
    def get_all(self) -> List[Permission]:
        return DEMO_PERMISSIONS

    def get_by_names(self, names: List[str]) -> List[Permission]:
        return [p for p in DEMO_PERMISSIONS if p.name in names]


class SessionRepository(BaseRepository):
    def create(self, user: UserProfile) -> str:
        session_id = str(uuid4())
        SESSIONS[session_id] = SessionRecord(
            session_id=session_id,
            user=user,
            expires_at=datetime.utcnow() + timedelta(seconds=SESSION_TTL_SECONDS),
        )
        return session_id

    def get(self, session_id: str) -> Optional[SessionRecord]:
        rec = SESSIONS.get(session_id)
        if not rec:
            return None
        if rec.expires_at < datetime.utcnow():
            del SESSIONS[session_id]
            return None
        return rec

    def delete(self, session_id: str):
        if session_id and session_id in SESSIONS:
            del SESSIONS[session_id]
