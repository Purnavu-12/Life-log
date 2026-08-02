"""
Database connection management
Uses SQLite by default, can be configured for PostgreSQL
"""

import sqlite3
import os
from typing import Generator
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Database path from environment or default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/lifelog.db")

# Check if using SQLite
USE_SQLITE = DATABASE_URL.startswith("sqlite")

# For SQLite, extract the path
if USE_SQLITE:
    # Remove sqlite:/// prefix
    DB_PATH = DATABASE_URL.replace("sqlite:///", "")
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Get database connection
    Yields a SQLite connection
    """
    if not USE_SQLITE:
        raise NotImplementedError("PostgreSQL not yet implemented. Use SQLite for now.")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


def init_db():
    """
    Initialize database with required tables
    """
    if not USE_SQLITE:
        logger.warning("PostgreSQL initialization not implemented yet")
        return
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                full_name TEXT,
                hashed_password TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                is_superuser INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT,
                last_login TEXT
            )
        """)
        
        # User settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT PRIMARY KEY,
                theme TEXT DEFAULT 'dark',
                email_notifications INTEGER DEFAULT 1,
                auto_create_events INTEGER DEFAULT 1,
                google_calendar_enabled INTEGER DEFAULT 0,
                gmail_enabled INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT,
                sentiment TEXT,
                tags TEXT DEFAULT '[]',
                topics TEXT DEFAULT '[]',
                tasks TEXT DEFAULT '[]',
                people TEXT DEFAULT '[]',
                dates TEXT DEFAULT '[]',
                action_items TEXT DEFAULT '[]',
                filename TEXT,
                source TEXT DEFAULT 'audio',
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                duration REAL,
                word_count INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Google credentials table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS google_credentials (
                user_id TEXT PRIMARY KEY,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                token_type TEXT DEFAULT 'Bearer',
                expires_at TEXT NOT NULL,
                scopes TEXT DEFAULT '[]',
                google_user_id TEXT,
                email TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Proposed actions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proposed_actions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                action_type TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'pending',
                confidence REAL DEFAULT 1.0,
                memory_id TEXT,
                related_entities TEXT DEFAULT '[]',
                scheduled_time TEXT,
                duration_minutes INTEGER,
                location TEXT,
                recipients TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                rejection_reason TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
            )
        """)
        
        # Audit logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT,
                description TEXT NOT NULL,
                details TEXT DEFAULT '{}',
                ip_address TEXT,
                user_agent TEXT,
                success INTEGER DEFAULT 1,
                error_message TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_user_id 
            ON memories(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_timestamp 
            ON memories(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email 
            ON users(email)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_proposed_actions_user_id 
            ON proposed_actions(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_proposed_actions_status 
            ON proposed_actions(status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_proposed_actions_memory_id 
            ON proposed_actions(memory_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_proposed_actions_created_at 
            ON proposed_actions(created_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id 
            ON audit_logs(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at 
            ON audit_logs(created_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_logs_action 
            ON audit_logs(action)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_type 
            ON audit_logs(entity_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_id 
            ON audit_logs(entity_id)
        """)
        
        logger.info("Database initialized successfully")


# Initialize database on import
init_db()
