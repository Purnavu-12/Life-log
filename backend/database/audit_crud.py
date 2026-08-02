"""
CRUD operations for audit logs
"""

import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging
from uuid import uuid4

from models.audit import (
    AuditLogCreate, 
    AuditLogResponse,
    AuditAction,
    AuditEntityType
)
from database.connection import get_db

logger = logging.getLogger(__name__)


def create_audit_log(log_data: AuditLogCreate) -> AuditLogResponse:
    """Create a new audit log entry"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        audit_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        
        cursor.execute(
            """
            INSERT INTO audit_logs (
                id, user_id, action, entity_type, entity_id, 
                description, details, ip_address, user_agent, 
                success, error_message, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                audit_id,
                log_data.user_id,
                log_data.action.value,
                log_data.entity_type.value,
                log_data.entity_id,
                log_data.description,
                json.dumps(log_data.details or {}),
                log_data.ip_address,
                log_data.user_agent,
                log_data.success,
                log_data.error_message,
                now
            )
        )
        
        logger.info(f"Created audit log: {audit_id} - {log_data.action.value} {log_data.entity_type.value}")
        
        # Return the created log
        return get_audit_log(audit_id)


def get_audit_log(log_id: str) -> Optional[AuditLogResponse]:
    """Get a specific audit log by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM audit_logs WHERE id = ?
            """,
            (log_id,)
        )
        row = cursor.fetchone()
        if row:
            return _row_to_audit_response(row)
        return None


def get_audit_logs(
    user_id: Optional[str] = None,
    action: Optional[AuditAction] = None,
    entity_type: Optional[AuditEntityType] = None,
    entity_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    success: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0
) -> List[AuditLogResponse]:
    """Get audit logs with optional filters"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM audit_logs
        """
        params = []
        
        conditions = []
        
        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
        
        if action:
            conditions.append("action = ?")
            params.append(action.value)
            
        if entity_type:
            conditions.append("entity_type = ?")
            params.append(entity_type.value)
            
        if entity_id:
            conditions.append("entity_id = ?")
            params.append(entity_id)
            
        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date)
            
        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date)
            
        if success is not None:
            conditions.append("success = ?")
            params.append(int(success))
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        
        logs = []
        for row in cursor.fetchall():
            log = _row_to_audit_response(row)
            if log:
                logs.append(log)
        
        return logs


def get_audit_logs_by_user(user_id: str, limit: int = 50) -> List[AuditLogResponse]:
    """Get audit logs for a specific user"""
    return get_audit_logs(user_id=user_id, limit=limit)


def get_recent_audit_logs(limit: int = 20) -> List[AuditLogResponse]:
    """Get most recent audit logs"""
    return get_audit_logs(limit=limit)


def delete_audit_logs_by_user(user_id: str) -> int:
    """Delete all audit logs for a specific user (for privacy compliance)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM audit_logs WHERE user_id = ?
            """,
            (user_id,)
        )
        
        count = cursor.rowcount
        logger.info(f"Deleted {count} audit logs for user: {user_id}")
        return count


def delete_audit_logs_older_than(days: int) -> int:
    """Delete audit logs older than a certain number of days"""
    from datetime import timedelta
    
    cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM audit_logs WHERE created_at < ?
            """,
            (cutoff_date,)
        )
        
        count = cursor.rowcount
        logger.info(f"Deleted {count} audit logs older than {days} days")
        return count


def get_audit_stats() -> Dict[str, Any]:
    """Get statistics about audit logs"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        stats = {}
        
        # Total count
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        row = cursor.fetchone()
        stats["total_logs"] = row[0] if row else 0
        
        # Count by action
        cursor.execute("SELECT action, COUNT(*) FROM audit_logs GROUP BY action")
        actions = {}
        for row in cursor.fetchall():
            actions[row["action"]] = row["COUNT(*)"]
        stats["by_action"] = actions
        
        # Count by entity type
        cursor.execute("SELECT entity_type, COUNT(*) FROM audit_logs GROUP BY entity_type")
        entity_types = {}
        for row in cursor.fetchall():
            entity_types[row["entity_type"]] = row["COUNT(*)"]
        stats["by_entity_type"] = entity_types
        
        # Count by success status
        cursor.execute("SELECT success, COUNT(*) FROM audit_logs GROUP BY success")
        success_stats = {}
        for row in cursor.fetchall():
            success_stats["success" if row["success"] else "failed"] = row["COUNT(*)"]
        stats["by_success"] = success_stats
        
        # Recent errors
        cursor.execute(
            """
            SELECT description, error_message, created_at 
            FROM audit_logs 
            WHERE success = 0 
            ORDER BY created_at DESC 
            LIMIT 5
            """
        )
        errors = []
        for row in cursor.fetchall():
            errors.append({
                "description": row["description"],
                "error_message": row["error_message"],
                "created_at": row["created_at"]
            })
        stats["recent_errors"] = errors
        
        return stats


def _row_to_audit_response(row: sqlite3.Row) -> AuditLogResponse:
    """Convert database row to AuditLogResponse"""
    return AuditLogResponse(
        id=row["id"],
        user_id=row["user_id"],
        action=AuditAction(row["action"]),
        entity_type=AuditEntityType(row["entity_type"]),
        entity_id=row["entity_id"],
        description=row["description"],
        details=json.loads(row["details"] or "{}"),
        ip_address=row["ip_address"],
        user_agent=row["user_agent"],
        success=bool(row["success"]),
        error_message=row["error_message"],
        created_at=row["created_at"]
    )