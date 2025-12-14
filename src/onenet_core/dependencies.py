from fastapi import Request, Depends, Cookie
from typing import List, Optional
from sqlalchemy.orm import Session
from .schemas import UserRead
from .database import get_db
from .utils.security import get_session_from_db, create_user_read_from_orm
from .exceptions import APIError
from .logger import get_logger, mask_session_id, get_client_ip

logger = get_logger(__name__)

def get_current_user(
    request: Request, 
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> UserRead:
    """Get current user from session cookie"""
    client_ip = get_client_ip(request)
    path = request.url.path
    
    logger.info(f"Authentication attempt from IP: {client_ip}, Path: {path}")
    
    if not session_id:
        logger.error(
            f"Authentication failed: No session cookie provided "
            f"(IP: {client_ip}, Path: {path})"
        )
        raise APIError(
            status_code=401, error_code="AUTH-003", message="Not authenticated"
        )
    
    logger.debug(f"Session cookie present: {mask_session_id(session_id)} (IP: {client_ip})")
    
    session = get_session_from_db(db, session_id)
    if not session:
        logger.error(
            f"Authentication failed: Session not found or expired "
            f"(Session: {mask_session_id(session_id)}, IP: {client_ip}, Path: {path})"
        )
        raise APIError(
            status_code=401, error_code="AUTH-002", message="Session expired"
        )

    user = create_user_read_from_orm(session.user)
    logger.info(
        f"Authentication successful for user: {user.email} (ID: {user.id}, "
        f"IP: {client_ip}, Roles: {user.roles})"
    )
    
    return user


def require_permissions(required: List[str]):
    def dependency(user: UserRead = Depends(get_current_user)):
        user_perms = set(user.permissions)
        
        logger.debug(
            f"Permission check for user {user.email}: "
            f"Required: {required}, Available: {sorted(user_perms)}"
        )
        
        for p in required:
            if p not in user_perms:
                logger.warning(
                    f"Permission denied for user {user.email}: "
                    f"Missing permission '{p}'. User has: {sorted(user_perms)}"
                )
                raise APIError(
                    status_code=403,
                    error_code="PERM-001",
                    message=f"Permission denied: {p} required",
                )
        
        logger.debug(f"Permission check passed for user {user.email}")
        return user

    return dependency
