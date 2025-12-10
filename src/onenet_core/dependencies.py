from fastapi import Request, Depends, Cookie
from typing import List, Optional
from sqlalchemy.orm import Session
from .schemas import UserRead
from .database import get_db
from .utils.security import get_session_from_db, create_user_read_from_orm
from .exceptions import APIError

def get_current_user(
    request: Request, 
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> UserRead:
    """Get current user from session cookie"""
    if not session_id:
        raise APIError(
            status_code=401, error_code="AUTH-003", message="Not authenticated"
        )
    
    session = get_session_from_db(db, session_id)
    if not session:
        raise APIError(
            status_code=401, error_code="AUTH-002", message="Session expired"
        )

    return create_user_read_from_orm(session.user)


def require_permissions(required: List[str]):
    def dependency(user: UserRead = Depends(get_current_user)):
        user_perms = set(user.permissions)
        for p in required:
            if p not in user_perms:
                raise APIError(
                    status_code=403,
                    error_code="PERM-001",
                    message=f"Permission denied: {p} required",
                )
        return user

    return dependency
