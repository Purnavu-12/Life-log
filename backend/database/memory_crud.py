"""
CRUD operations for memories
"""

import sqlite3
import json
import uuid
from typing import Optional, List
from datetime import datetime
import logging

from models.memory import Memory, MemoryCreate, MemoryResponse, MemoryUpdate
from database.connection import get_db

logger = logging.getLogger(__name__)


def _serialize_lists(data: dict) -> dict:
    """Serialize list fields to JSON strings for database storage"""
    if "tags" in data and isinstance(data["tags"], list):
        data["tags"] = json.dumps(data["tags"])
    if "topics" in data and isinstance(data["topics"], list):
        data["topics"] = json.dumps(data["topics"])
    if "tasks" in data and isinstance(data["tasks"], list):
        data["tasks"] = json.dumps(data["tasks"])
    if "people" in data and isinstance(data["people"], list):
        data["people"] = json.dumps(data["people"])
    if "dates" in data and isinstance(data["dates"], list):
        data["dates"] = json.dumps(data["dates"])
    if "action_items" in data and isinstance(data["action_items"], list):
        data["action_items"] = json.dumps(data["action_items"])
    return data


def _deserialize_memory(row: sqlite3.Row) -> Memory:
    """Deserialize database row to Memory object"""
    return Memory(
        id=row["id"],
        user_id=row["user_id"],
        content=row["content"],
        summary=row["summary"],
        sentiment=row["sentiment"],
        tags=json.loads(row["tags"] or "[]"),
        topics=json.loads(row["topics"] or "[]"),
        tasks=json.loads(row["tasks"] or "[]"),
        people=json.loads(row["people"] or "[]"),
        dates=json.loads(row["dates"] or "[]"),
        action_items=json.loads(row["action_items"] or "[]"),
        filename=row["filename"],
        source=row["source"],
        timestamp=row["timestamp"],
        duration=row["duration"],
        word_count=row["word_count"]
    )


def get_memory_by_id(memory_id: str) -> Optional[Memory]:
    """Get a memory by its ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM memories WHERE id = ?",
            (memory_id,)
        )
        row = cursor.fetchone()
        if row:
            return _deserialize_memory(row)
    return None


def get_memories_by_user(user_id: str, limit: int = 10, offset: int = 0) -> List[Memory]:
    """Get all memories for a specific user with pagination"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM memories 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset)
        )
        memories = []
        for row in cursor.fetchall():
            memories.append(_deserialize_memory(row))
        return memories


def create_memory(memory_data: MemoryCreate, user_id: str) -> Memory:
    """Create a new memory"""
    data = memory_data.model_dump()
    data = _serialize_lists(data)
    
    # Generate ID if not provided
    memory_id = data.get("id") or str(uuid.uuid4())
    data["id"] = memory_id
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO memories (
                id, user_id, content, summary, sentiment, tags, topics, 
                tasks, people, dates, action_items, filename, source, 
                timestamp, duration, word_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                user_id,
                data.get("content"),
                data.get("summary"),
                data.get("sentiment"),
                data.get("tags", "[]"),
                data.get("topics", "[]"),
                data.get("tasks", "[]"),
                data.get("people", "[]"),
                data.get("dates", "[]"),
                data.get("action_items", "[]"),
                data.get("filename"),
                data.get("source", "audio"),
                data.get("timestamp", datetime.utcnow().isoformat()),
                data.get("duration"),
                data.get("word_count")
            )
        )

        # Fetch the created memory using the same connection
        cursor.execute(
            "SELECT * FROM memories WHERE id = ?",
            (memory_id,)
        )
        row = cursor.fetchone()

        if row:
            memory = _deserialize_memory(row)
            logger.info(f"Created memory: {memory_id} for user: {user_id}")
            return memory
        
        raise ValueError("Failed to create memory")


def update_memory(memory_id: str, update_data: MemoryUpdate, user_id: str) -> Optional[Memory]:
    """Update a memory"""
    data = update_data.model_dump(exclude_unset=True)
    data = _serialize_lists(data)
    
    if not data:
        return get_memory_by_id(memory_id)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Build update query
        set_clauses = []
        values = []
        
        if "content" in data:
            set_clauses.append("content = ?")
            values.append(data["content"])
        if "summary" in data:
            set_clauses.append("summary = ?")
            values.append(data["summary"])
        if "sentiment" in data:
            set_clauses.append("sentiment = ?")
            values.append(data["sentiment"])
        if "tags" in data:
            set_clauses.append("tags = ?")
            values.append(data["tags"])
        if "topics" in data:
            set_clauses.append("topics = ?")
            values.append(data["topics"])
        if "tasks" in data:
            set_clauses.append("tasks = ?")
            values.append(data["tasks"])
        if "people" in data:
            set_clauses.append("people = ?")
            values.append(data["people"])
        if "dates" in data:
            set_clauses.append("dates = ?")
            values.append(data["dates"])
        if "action_items" in data:
            set_clauses.append("action_items = ?")
            values.append(data["action_items"])
        if "filename" in data:
            set_clauses.append("filename = ?")
            values.append(data["filename"])
        if "source" in data:
            set_clauses.append("source = ?")
            values.append(data["source"])
        if "duration" in data:
            set_clauses.append("duration = ?")
            values.append(data["duration"])
        if "word_count" in data:
            set_clauses.append("word_count = ?")
            values.append(data["word_count"])
        
        if set_clauses:
            values.append(memory_id)
            values.append(user_id)  # Ensure user owns the memory
            
            query = f"UPDATE memories SET {', '.join(set_clauses)} WHERE id = ? AND user_id = ?"
            cursor.execute(query, values)
        
        # Fetch updated memory
        return get_memory_by_id(memory_id)


def delete_memory(memory_id: str, user_id: str) -> bool:
    """Delete a memory"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM memories WHERE id = ? AND user_id = ?",
            (memory_id, user_id)
        )
        return cursor.rowcount > 0


def search_memories_by_user(user_id: str, query: str, limit: int = 10) -> List[Memory]:
    """Search memories by content for a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Full-text search (SQLite FTS5 would be better but requires separate setup)
        search_pattern = f"%{query}%"
        cursor.execute(
            """
            SELECT * FROM memories 
            WHERE user_id = ? AND (content LIKE ? OR summary LIKE ?)
            ORDER BY timestamp DESC 
            LIMIT ?
            """,
            (user_id, search_pattern, search_pattern, limit)
        )
        memories = []
        for row in cursor.fetchall():
            memories.append(_deserialize_memory(row))
        return memories


def get_memories_count_by_user(user_id: str) -> int:
    """Get total count of memories for a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM memories WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        return row["count"] if row else 0
