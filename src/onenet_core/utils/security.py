from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
from sqlalchemy.orm import Session
from ..models.session import Session as SessionModel
from ..models.user import User
from ..schemas import UserRead
from ..config import SESSION_TTL_SECONDS
from ..logger import get_logger, mask_session_id

logger = get_logger(__name__)

def _now() -> datetime:
    return datetime.utcnow()

def create_user_read_from_orm(user: User) -> UserRead:
    """Convert SQLAlchemy User to Pydantic UserRead"""
    role_names = [r.name for r in user.roles]
    perms = set()
    for r in user.roles:
        for p in r.permissions:
            perms.add(p.name)
    
    return UserRead(
        id=user.id,
        email=user.email,
        name=user.name,
        is_active=user.is_active,
        roles=role_names,
        permissions=list(perms),
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login
    )

def create_session_for_user(db: Session, user: User) -> str:
    """Create a new session for user in DB"""
    session_id = str(uuid4())
    expires = _now() + timedelta(seconds=SESSION_TTL_SECONDS)
    
    db_session = SessionModel(
        session_id=session_id,
        user_id=user.id,
        expires_at=expires
    )
    db.add(db_session)
    db.commit()
    
    logger.info(
        f"Session created for user {user.email} (ID: {user.id}). "
        f"Session: {mask_session_id(session_id)}, Expires: {expires}"
    )
    
    return session_id

def get_session_from_db(db: Session, session_id: Optional[str]) -> Optional[SessionModel]:
    """Get session from DB, delete if expired"""
    if not session_id:
        logger.debug("Session lookup failed: No session_id provided")
        return None
    
    logger.debug(f"Looking up session: {mask_session_id(session_id)}")
    
    session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    if not session:
        logger.warning(f"Session not found in database: {mask_session_id(session_id)}")
        return None
    
    if session.expires_at < _now():
        logger.warning(
            f"Session expired: {mask_session_id(session_id)} "
            f"(User: {session.user.email}, Expired at: {session.expires_at}). Deleting from database."
        )
        db.delete(session)
        db.commit()
        return None
    
    logger.debug(
        f"Session found and valid: {mask_session_id(session_id)} "
        f"(User: {session.user.email}, Expires: {session.expires_at})"
    )
    
    return session

def delete_session_from_db(db: Session, session_id: Optional[str]):
    """Delete session from DB"""
    if not session_id:
        logger.debug("Session deletion skipped: No session_id provided")
        return
    
    session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    if session:
        logger.info(
            f"Session deleted: {mask_session_id(session_id)} "
            f"(User: {session.user.email})"
        )
        db.delete(session)
        db.commit()
    else:
        logger.debug(f"Session deletion failed: Session not found {mask_session_id(session_id)}")
