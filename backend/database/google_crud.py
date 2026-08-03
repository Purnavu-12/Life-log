"""
CRUD operations for Google OAuth credentials
"""

import sqlite3
from typing import Optional
from datetime import datetime
import json
import logging

from models.google import GoogleCredentials
from database.connection import get_db

logger = logging.getLogger(__name__)


def get_google_credentials(user_id: str) -> Optional[GoogleCredentials]:
    """Get Google OAuth credentials for a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM google_credentials WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return GoogleCredentials(
                user_id=row["user_id"],
                access_token=row["access_token"],
                refresh_token=row["refresh_token"],
                token_type=row["token_type"],
                expires_at=row["expires_at"],
                scopes=json.loads(row["scopes"] or "[]"),
                google_user_id=row["google_user_id"],
                email=row["email"]
            )
    return None


def save_google_credentials(credentials: GoogleCredentials) -> GoogleCredentials:
    """Save or update Google OAuth credentials for a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if credentials already exist
        existing = get_google_credentials(credentials.user_id)
        
        if existing:
            # Update existing
            cursor.execute(
                """
                UPDATE google_credentials SET
                    access_token = ?,
                    refresh_token = ?,
                    token_type = ?,
                    expires_at = ?,
                    scopes = ?,
                    google_user_id = ?,
                    email = ?
                WHERE user_id = ?
                """,
                (
                    credentials.access_token,
                    credentials.refresh_token,
                    credentials.token_type,
                    credentials.expires_at.isoformat() if isinstance(credentials.expires_at, datetime) else credentials.expires_at,
                    json.dumps(credentials.scopes),
                    credentials.google_user_id,
                    credentials.email,
                    credentials.user_id
                )
            )
            logger.info(f"Updated Google credentials for user: {credentials.user_id}")
        else:
            # Insert new
            cursor.execute(
                """
                INSERT INTO google_credentials (
                    user_id, access_token, refresh_token, token_type,
                    expires_at, scopes, google_user_id, email
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    credentials.user_id,
                    credentials.access_token,
                    credentials.refresh_token,
                    credentials.token_type,
                    credentials.expires_at.isoformat() if isinstance(credentials.expires_at, datetime) else credentials.expires_at,
                    json.dumps(credentials.scopes),
                    credentials.google_user_id,
                    credentials.email
                )
            )
            logger.info(f"Saved Google credentials for user: {credentials.user_id}")
        
        return get_google_credentials(credentials.user_id)


def delete_google_credentials(user_id: str) -> bool:
    """Delete Google OAuth credentials for a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM google_credentials WHERE user_id = ?",
            (user_id,)
        )
        return cursor.rowcount > 0


def is_google_connected(user_id: str) -> bool:
    """Check if a user has Google connected"""
    return get_google_credentials(user_id) is not None


def get_google_enabled_users() -> list:
    """Get all users with Google connected"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT gc.user_id, gc.email, gc.scopes, u.username, u.full_name
            FROM google_credentials gc
            JOIN users u ON gc.user_id = u.id
            """
        )
        users = []
        for row in cursor.fetchall():
            users.append({
                "user_id": row["user_id"],
                "email": row["email"],
                "scopes": json.loads(row["scopes"]),
                "username": row["username"],
                "full_name": row["full_name"]
            })
        return users


def is_google_connected(user_id: str) -> bool:
    """Return True if the user has valid Google OAuth credentials stored."""
    creds = get_google_credentials(user_id)
    return creds is not None and bool(creds.access_token)
