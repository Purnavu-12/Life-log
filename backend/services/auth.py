"""
Authentication service for JWT-based auth
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from models.user import User, UserCreate, UserInDB, UserResponse
from models.token import Token, TokenData

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET", "fallback-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()


class AuthService:
    """Service for handling authentication"""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password for storing"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def decode_token(self, token: str) -> TokenData:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return TokenData(
                username=payload.get("sub"),
                user_id=payload.get("user_id"),
                email=payload.get("email")
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def refresh_access_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token"""
        try:
            # Decode refresh token (without exp check)
            payload = jwt.decode(
                refresh_token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Create new access token
            token_data = {
                "sub": payload.get("sub"),
                "user_id": payload.get("user_id"),
                "email": payload.get("email")
            }
            
            access_token = self.create_access_token(token_data)
            new_refresh_token = self.create_refresh_token(token_data)
            
            return Token(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired. Please login again.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token. Please login again.",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user by email and password"""
        from database import get_user_by_email, update_user
        user = get_user_by_email(email)
        if user and self.verify_password(password, user.hashed_password):
            # Update last login
            update_user(user.id, {"update_last_login": True})
            return user
        return None

    def authenticate_user_by_username(self, username: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user by username and password (for local/installed-app logins)"""
        from database import get_user_by_username, update_user
        user = get_user_by_username(username)
        if user and self.verify_password(password, user.hashed_password):
            update_user(user.id, {"update_last_login": True})
            return user
        return None
    
    def register_user(self, user_data: UserCreate) -> UserInDB:
        """Register a new user"""
        from database import get_user_by_email, get_user_by_username, create_user
        # Check if user already exists
        if get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        if get_user_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        return create_user(user_data)
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
        """Get the current user from JWT token"""
        from database import get_user_by_id
        try:
            token_data = self.decode_token(credentials.credentials)
            user = get_user_by_id(token_data.user_id)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def get_current_active_user(self, current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        """Get current active user (checks is_active flag)"""
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        return current_user


# Singleton instance
auth_service = AuthService()


# Dependency functions for FastAPI
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    """FastAPI dependency for current user"""
    return auth_service.get_current_user(credentials)


def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """FastAPI dependency for current active user"""
    return auth_service.get_current_active_user(current_user)
