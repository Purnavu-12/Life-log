"""
Proposed actions model for AI-generated suggestions
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ActionStatus(str, Enum):
    """Status of a proposed action"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class ActionType(str, Enum):
    """Type of proposed action"""
    CREATE_EVENT = "create_event"
    SEND_EMAIL = "send_email"
    CREATE_TASK = "create_task"
    SET_REMINDER = "set_reminder"
    ADD_NOTE = "add_note"
    SYNC_CALENDAR = "sync_calendar"


class ActionPriority(str, Enum):
    """Priority level for actions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ProposedActionBase(BaseModel):
    """Base model for proposed actions"""
    title: str
    description: Optional[str] = None
    action_type: ActionType
    priority: ActionPriority = ActionPriority.MEDIUM
    status: ActionStatus = ActionStatus.PENDING
    confidence: float = 1.0  # AI confidence score (0-1)
    
class ProposedActionCreate(ProposedActionBase):
    """Model for creating proposed actions"""
    # Additional context for the action
    memory_id: Optional[str] = None
    related_entities: Optional[List[str]] = Field(default_factory=list)  # people, dates, topics
    scheduled_time: Optional[str] = None  # ISO datetime string
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    recipients: Optional[List[str]] = Field(default_factory=list)  # for emails
    
class ProposedActionResponse(ProposedActionBase):
    """Model for proposed action responses"""
    id: str
    user_id: str
    memory_id: Optional[str] = None
    related_entities: List[str] = Field(default_factory=list)
    scheduled_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    recipients: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    class Config:
        from_attributes = True


class ActionApprovalRequest(BaseModel):
    """Model for approving/rejecting actions.

    `action_id` is accepted here for backwards compatibility but is also taken
    from the URL path, so it is optional.
    """
    action_id: Optional[str] = None
    approve: bool = True
    rejection_reason: Optional[str] = None
    scheduled_time: Optional[str] = None  # Allow rescheduling on approval
    

class ActionCompletionRequest(BaseModel):
    """Model for marking actions as completed"""
    action_id: str
    notes: Optional[str] = None
    

class ActionFilter(BaseModel):
    """Model for filtering actions"""
    status: Optional[ActionStatus] = None
    action_type: Optional[ActionType] = None
    priority: Optional[ActionPriority] = None
    limit: int = 20
    offset: int = 0