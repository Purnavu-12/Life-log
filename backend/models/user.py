"""
User models for authentication and user management
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30)
    full_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=8)


class User(UserBase):
    """User model with ID and timestamps"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserInDB(User):
    """User model with hashed password (for internal use)"""
    hashed_password: str


class UserResponse(BaseModel):
    """User model for API responses (excluding sensitive data)"""
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True
