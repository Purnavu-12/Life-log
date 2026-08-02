"""
CRUD operations for proposed actions
"""

import sqlite3
from typing import Optional, List
from datetime import datetime
import json
import logging
from uuid import uuid4

from models.action import (
    ProposedActionCreate, 
    ProposedActionResponse, 
    ActionStatus,
    ActionType,
    ActionPriority
)
from database.connection import get_db

logger = logging.getLogger(__name__)


def create_proposed_action(
    action_data: ProposedActionCreate, 
    user_id: str
) -> ProposedActionResponse:
    """Create a new proposed action"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        action_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        
        cursor.execute(
            """
            INSERT INTO proposed_actions (
                id, user_id, title, description, action_type, priority, 
                status, confidence, memory_id, related_entities, 
                scheduled_time, duration_minutes, location, recipients,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                action_id,
                user_id,
                action_data.title,
                action_data.description,
                action_data.action_type.value,
                action_data.priority.value,
                action_data.status.value,
                action_data.confidence,
                action_data.memory_id,
                json.dumps(action_data.related_entities or []),
                action_data.scheduled_time,
                action_data.duration_minutes,
                action_data.location,
                json.dumps(action_data.recipients or []),
                now,
                now
            )
        )
        
        logger.info(f"Created proposed action: {action_id} for user: {user_id}")
        
        # Return the created action
        return get_proposed_action(action_id, user_id)


def get_proposed_action(action_id: str, user_id: str) -> Optional[ProposedActionResponse]:
    """Get a specific proposed action by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM proposed_actions 
            WHERE id = ? AND user_id = ?
            """,
            (action_id, user_id)
        )
        row = cursor.fetchone()
        if row:
            return _row_to_action_response(row)
        return None


def get_proposed_actions(
    user_id: str,
    status: Optional[ActionStatus] = None,
    action_type: Optional[ActionType] = None,
    priority: Optional[ActionPriority] = None,
    limit: int = 20,
    offset: int = 0
) -> List[ProposedActionResponse]:
    """Get proposed actions for a user with optional filters"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM proposed_actions 
            WHERE user_id = ?
        """
        params = [user_id]
        
        # Add filters
        if status:
            query += " AND status = ?"
            params.append(status.value)
        if action_type:
            query += " AND action_type = ?"
            params.append(action_type.value)
        if priority:
            query += " AND priority = ?"
            params.append(priority.value)
            
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        
        actions = []
        for row in cursor.fetchall():
            action = _row_to_action_response(row)
            if action:
                actions.append(action)
        
        return actions


def get_pending_actions(user_id: str, limit: int = 20) -> List[ProposedActionResponse]:
    """Get all pending actions for a user"""
    return get_proposed_actions(
        user_id=user_id,
        status=ActionStatus.PENDING,
        limit=limit
    )


def get_actions_requiring_approval(user_id: str, limit: int = 20) -> List[ProposedActionResponse]:
    """Get actions that need user approval (pending status)"""
    return get_pending_actions(user_id, limit)


def update_proposed_action(
    action_id: str, 
    user_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[ActionStatus] = None,
    priority: Optional[ActionPriority] = None,
    scheduled_time: Optional[str] = None,
    location: Optional[str] = None,
    recipients: Optional[List[str]] = None
) -> Optional[ProposedActionResponse]:
    """Update a proposed action"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Build update query
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if status is not None:
            updates.append("status = ?")
            params.append(status.value)
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority.value)
        if scheduled_time is not None:
            updates.append("scheduled_time = ?")
            params.append(scheduled_time)
        if location is not None:
            updates.append("location = ?")
            params.append(location)
        if recipients is not None:
            updates.append("recipients = ?")
            params.append(json.dumps(recipients))
            
        if not updates:
            return get_proposed_action(action_id, user_id)
            
        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        
        params.extend([action_id, user_id])
        
        query = f"""
            UPDATE proposed_actions 
            SET {', '.join(updates)}
            WHERE id = ? AND user_id = ?
        """
        
        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            return None
            
        logger.info(f"Updated proposed action: {action_id}")
        return get_proposed_action(action_id, user_id)


def approve_action(
    action_id: str, 
    user_id: str, 
    scheduled_time: Optional[str] = None
) -> Optional[ProposedActionResponse]:
    """Approve a proposed action"""
    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        
        # Clear rejection reason if previously rejected
        cursor.execute(
            """
            UPDATE proposed_actions 
            SET status = ?, updated_at = ?, rejection_reason = NULL, completed_at = NULL
            WHERE id = ? AND user_id = ?
            """,
            (ActionStatus.APPROVED.value, now, action_id, user_id)
        )
        
        # Update scheduled time if provided
        if scheduled_time:
            cursor.execute(
                """
                UPDATE proposed_actions 
                SET scheduled_time = ? 
                WHERE id = ? AND user_id = ?
                """,
                (scheduled_time, action_id, user_id)
            )
        
        if cursor.rowcount == 0:
            return None
            
        logger.info(f"Approved action: {action_id}")
        return get_proposed_action(action_id, user_id)


def reject_action(
    action_id: str, 
    user_id: str, 
    rejection_reason: Optional[str] = None
) -> Optional[ProposedActionResponse]:
    """Reject a proposed action"""
    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        
        cursor.execute(
            """
            UPDATE proposed_actions 
            SET status = ?, updated_at = ?, rejection_reason = ?
            WHERE id = ? AND user_id = ?
            """,
            (ActionStatus.REJECTED.value, now, rejection_reason, action_id, user_id)
        )
        
        if cursor.rowcount == 0:
            return None
            
        logger.info(f"Rejected action: {action_id} with reason: {rejection_reason}")
        return get_proposed_action(action_id, user_id)


def complete_action(
    action_id: str, 
    user_id: str, 
    notes: Optional[str] = None
) -> Optional[ProposedActionResponse]:
    """Mark a proposed action as completed"""
    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        
        cursor.execute(
            """
            UPDATE proposed_actions 
            SET status = ?, updated_at = ?, completed_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (ActionStatus.COMPLETED.value, now, now, action_id, user_id)
        )
        
        if cursor.rowcount == 0:
            return None
            
        logger.info(f"Completed action: {action_id}")
        return get_proposed_action(action_id, user_id)


def delete_proposed_action(action_id: str, user_id: str) -> bool:
    """Delete a proposed action"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM proposed_actions WHERE id = ? AND user_id = ?
            """,
            (action_id, user_id)
        )
        
        if cursor.rowcount == 0:
            return False
            
        logger.info(f"Deleted proposed action: {action_id}")
        return True


def delete_actions_by_memory(memory_id: str, user_id: str) -> int:
    """Delete all actions associated with a memory"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM proposed_actions WHERE memory_id = ? AND user_id = ?
            """,
            (memory_id, user_id)
        )
        
        logger.info(f"Deleted {cursor.rowcount} actions for memory: {memory_id}")
        return cursor.rowcount


def get_action_count_by_status(user_id: str) -> dict:
    """Get count of actions by status for a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        counts = {}
        for status in [s.value for s in ActionStatus]:
            cursor.execute(
                """
                SELECT COUNT(*) as count FROM proposed_actions 
                WHERE user_id = ? AND status = ?
                """,
                (user_id, status)
            )
            row = cursor.fetchone()
            counts[status] = row["count"] if row else 0
            
        return counts


def _row_to_action_response(row: sqlite3.Row) -> ProposedActionResponse:
    """Convert database row to ProposedActionResponse"""
    return ProposedActionResponse(
        id=row["id"],
        user_id=row["user_id"],
        title=row["title"],
        description=row["description"],
        action_type=ActionType(row["action_type"]),
        priority=ActionPriority(row["priority"]),
        status=ActionStatus(row["status"]),
        confidence=row["confidence"],
        memory_id=row["memory_id"],
        related_entities=json.loads(row["related_entities"] or "[]"),
        scheduled_time=row["scheduled_time"],
        duration_minutes=row["duration_minutes"],
        location=row["location"],
        recipients=json.loads(row["recipients"] or "[]"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        completed_at=row["completed_at"],
        rejection_reason=row["rejection_reason"]
    )