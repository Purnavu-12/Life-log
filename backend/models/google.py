"""
Google OAuth credentials model
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class GoogleCredentials(BaseModel):
    """Google OAuth credentials stored per user"""
    user_id: str
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: datetime
    scopes: list = Field(default_factory=list)
    
    # Google-specific fields
    google_user_id: Optional[str] = None
    email: Optional[str] = None
    
    class Config:
        from_attributes = True


class GoogleTokenResponse(BaseModel):
    """Response from Google OAuth token endpoint"""
    access_token: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: str
    token_type: str = "Bearer"


class GoogleUserInfo(BaseModel):
    """Google user info from OAuth"""
    id: str
    email: str
    verified_email: bool
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    locale: Optional[str] = None
