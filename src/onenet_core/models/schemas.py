from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class UserProfile(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
    roles: List[str]
    permissions: List[str]
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class Role(BaseModel):
    id: int
    name: str
    description: Optional[str] = None


class Permission(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None


class SessionRecord(BaseModel):
    session_id: str
    user: UserProfile
    expires_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]
    message: str


class RegisterResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]
    message: str


class LogoutResponse(BaseModel):
    success: bool = True
    message: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordResponse(BaseModel):
    success: bool = True
    message: str


class UserCreateRequest(BaseModel):
    email: EmailStr
    name: str
    password: str = Field(..., min_length=8)
    roles: List[str] = []
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None


class RoleCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    permission_names: List[str] = []


class AssignRoleRequest(BaseModel):
    role_name: str


class WalletBalanceResponse(BaseModel):
    currency: str
    available: float
    ledger: float
    last_updated: datetime


class TransactionItem(BaseModel):
    id: str
    type: str
    amount: float
    currency: str
    description: str
    created_at: datetime


class TransactionListResponse(BaseModel):
    items: List[TransactionItem]


class FeatureFlag(BaseModel):
    name: str
    enabled: bool
    description: Optional[str] = None


class ConfigResponse(BaseModel):
    environment: str
    version: str
    feature_flags: List[FeatureFlag]


class HealthResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
