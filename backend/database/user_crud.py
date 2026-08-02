"""
CRUD operations for users
"""

import sqlite3
from typing import Optional
from datetime import datetime
import json
import logging

from models.user import User, UserCreate, UserResponse, UserInDB
from database.connection import get_db

logger = logging.getLogger(__name__)


def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Get user by email address"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )
        row = cursor.fetchone()
        if row:
            return UserInDB(
                id=row["id"],
                email=row["email"],
                username=row["username"],
                full_name=row["full_name"],
                is_active=bool(row["is_active"]),
                is_superuser=bool(row["is_superuser"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                last_login=row["last_login"],
                hashed_password=row["hashed_password"]
            )
    return None


def get_user_by_username(username: str) -> Optional[UserInDB]:
    """Get user by username"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        if row:
            return UserInDB(
                id=row["id"],
                email=row["email"],
                username=row["username"],
                full_name=row["full_name"],
                is_active=bool(row["is_active"]),
                is_superuser=bool(row["is_superuser"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                last_login=row["last_login"],
                hashed_password=row["hashed_password"]
            )
    return None


def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    """Get user by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return UserInDB(
                id=row["id"],
                email=row["email"],
                username=row["username"],
                full_name=row["full_name"],
                is_active=bool(row["is_active"]),
                is_superuser=bool(row["is_superuser"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                last_login=row["last_login"],
                hashed_password=row["hashed_password"]
            )
    return None


def create_user(user_data: UserCreate) -> UserInDB:
    """Create a new user"""
    from services.auth import auth_service
    import uuid
    
    hashed_password = auth_service.get_password_hash(user_data.password)
    user_id = str(uuid.uuid4())
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (id, email, username, full_name, hashed_password)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                user_data.email,
                user_data.username,
                user_data.full_name,
                hashed_password
            )
        )
        
        # Create default settings
        cursor.execute(
            """
            INSERT INTO user_settings (user_id)
            VALUES (?)
            """,
            (user_id,)
        )
        
        # Fetch the created user using the same connection
        cursor.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            user = UserInDB(
                id=row["id"],
                email=row["email"],
                username=row["username"],
                full_name=row["full_name"],
                is_active=bool(row["is_active"]),
                is_superuser=bool(row["is_superuser"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                last_login=row["last_login"],
                hashed_password=row["hashed_password"]
            )
            logger.info(f"Created user: {user.username} ({user.email})")
            return user
        
        raise ValueError("Failed to create user")


def update_user(user_id: str, update_data: dict) -> Optional[UserInDB]:
    """Update user information"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Build update query
        set_clauses = []
        values = []
        
        if "email" in update_data:
            set_clauses.append("email = ?")
            values.append(update_data["email"])
        if "username" in update_data:
            set_clauses.append("username = ?")
            values.append(update_data["username"])
        if "full_name" in update_data:
            set_clauses.append("full_name = ?")
            values.append(update_data["full_name"])
        if "is_active" in update_data:
            set_clauses.append("is_active = ?")
            values.append(int(update_data["is_active"]))
        if "is_superuser" in update_data:
            set_clauses.append("is_superuser = ?")
            values.append(int(update_data["is_superuser"]))
        if "hashed_password" in update_data:
            set_clauses.append("hashed_password = ?")
            values.append(update_data["hashed_password"])
        
        if set_clauses:
            set_clauses.append("updated_at = ?")
            values.append(datetime.utcnow().isoformat())
            values.append(user_id)
            
            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"
            cursor.execute(query, values)
        
        # Update last login if requested
        if update_data.get("update_last_login"):
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), user_id)
            )
        
        # Fetch updated user
        return get_user_by_id(user_id)


def delete_user(user_id: str) -> bool:
    """Delete a user and all their data"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,)
        )
        return cursor.rowcount > 0


def get_all_users(limit: int = 100, offset: int = 0) -> list:
    """Get all users with pagination"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        users = []
        for row in cursor.fetchall():
            users.append(UserResponse(
                id=row["id"],
                email=row["email"],
                username=row["username"],
                full_name=row["full_name"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                last_login=row["last_login"]
            ))
        return users
