"""
Audit log model for tracking user activities and system events
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AuditAction(str, Enum):
    """Types of audit actions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"
    SYNC = "sync"
    ERROR = "error"


class AuditEntityType(str, Enum):
    """Types of entities that can be audited"""
    USER = "user"
    MEMORY = "memory"
    ACTION = "action"
    GOOGLE_CREDENTIALS = "google_credentials"
    SETTINGS = "settings"
    SYSTEM = "system"


class AuditLogCreate(BaseModel):
    """Model for creating audit log entries"""
    user_id: str
    action: AuditAction
    entity_type: AuditEntityType
    entity_id: Optional[str] = None
    description: str
    details: Optional[dict] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class AuditLogResponse(BaseModel):
    """Model for audit log responses"""
    id: str
    user_id: str
    action: AuditAction
    entity_type: AuditEntityType
    entity_id: Optional[str] = None
    description: str
    details: dict = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditFilter(BaseModel):
    """Model for filtering audit logs"""
    user_id: Optional[str] = None
    action: Optional[AuditAction] = None
    entity_type: Optional[AuditEntityType] = None
    entity_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    success: Optional[bool] = None
    limit: int = 50
    offset: int = 0