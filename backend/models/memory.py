"""
Memory models for the LifeLog system
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


class MemoryBase(BaseModel):
    """Base memory model with core fields"""
    content: str = Field(..., min_length=1)
    summary: Optional[str] = None
    sentiment: Optional[str] = Field(None, pattern="^(positive|negative|neutral)$")
    tags: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    tasks: List[str] = Field(default_factory=list)
    people: List[str] = Field(default_factory=list)
    dates: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)


class MemoryCreate(MemoryBase):
    """Memory creation model"""
    filename: Optional[str] = None
    source: Optional[str] = Field(default="audio", pattern="^(audio|text|email|calendar)$")


class Memory(MemoryBase):
    """Full memory model with metadata"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    filename: Optional[str] = None
    source: str = Field(default="audio", pattern="^(audio|text|email|calendar)$")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration: Optional[float] = None  # Audio duration in seconds
    word_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class MemoryResponse(BaseModel):
    """Memory model for API responses"""
    id: str
    user_id: str
    content: str
    summary: Optional[str]
    sentiment: Optional[str]
    tags: List[str]
    topics: List[str]
    tasks: List[str]
    people: List[str]
    dates: List[str]
    action_items: List[str]
    filename: Optional[str]
    source: str
    timestamp: datetime
    duration: Optional[float]
    word_count: Optional[int]
    
    class Config:
        from_attributes = True


class MemoryUpdate(BaseModel):
    """Memory update model"""
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    tasks: Optional[List[str]] = None
    people: Optional[List[str]] = None
    dates: Optional[List[str]] = None
    action_items: Optional[List[str]] = None
