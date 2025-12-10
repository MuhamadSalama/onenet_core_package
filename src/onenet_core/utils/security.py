from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
from sqlalchemy.orm import Session
from ..models.session import Session as SessionModel
from ..models.user import User
from ..schemas import UserRead
from ..config import SESSION_TTL_SECONDS

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
    return session_id

def get_session_from_db(db: Session, session_id: Optional[str]) -> Optional[SessionModel]:
    """Get session from DB, delete if expired"""
    if not session_id:
        return None
    
    session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    if not session:
        return None
    
    if session.expires_at < _now():
        db.delete(session)
        db.commit()
        return None
    
    return session

def delete_session_from_db(db: Session, session_id: Optional[str]):
    """Delete session from DB"""
    if not session_id:
        return
    
    session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    if session:
        db.delete(session)
        db.commit()
