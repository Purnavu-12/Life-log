"""
Audit service for logging user activities and system events
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from models.audit import AuditLogCreate, AuditAction, AuditEntityType
from database import create_audit_log

logger = logging.getLogger(__name__)


class AuditService:
    """Service for creating audit log entries"""
    
    def __init__(self):
        pass
    
    def log(
        self,
        user_id: str,
        action: AuditAction,
        entity_type: AuditEntityType,
        description: str,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLogCreate]:
        """Create an audit log entry"""
        try:
            log_data = AuditLogCreate(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                description=description,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message
            )
            
            audit_log = create_audit_log(log_data)
            
            if not success:
                logger.warning(f"Audit log: {description} - ERROR: {error_message}")
            else:
                logger.debug(f"Audit log: {description}")
            
            return log_data
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            return None
    
    def log_memory_operation(
        self,
        user_id: str,
        action: AuditAction,
        memory_id: str,
        description: str = "",
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log memory-related operations"""
        if not description:
            description = f"{action.value} memory {memory_id}"
        
        return self.log(
            user_id=user_id,
            action=action,
            entity_type=AuditEntityType.MEMORY,
            entity_id=memory_id,
            description=description,
            success=success,
            error_message=error_message
        )
    
    def log_action_operation(
        self,
        user_id: str,
        action: AuditAction,
        action_id: str,
        description: str = "",
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log proposed action-related operations"""
        if not description:
            description = f"{action.value} action {action_id}"
        
        return self.log(
            user_id=user_id,
            action=action,
            entity_type=AuditEntityType.ACTION,
            entity_id=action_id,
            description=description,
            success=success,
            error_message=error_message
        )
    
    def log_user_operation(
        self,
        user_id: str,
        action: AuditAction,
        description: str = "",
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log user-related operations"""
        if not description:
            description = f"{action.value} user"
        
        return self.log(
            user_id=user_id,
            action=action,
            entity_type=AuditEntityType.USER,
            description=description,
            success=success,
            error_message=error_message
        )
    
    def log_google_operation(
        self,
        user_id: str,
        action: AuditAction,
        description: str = "",
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log Google integration operations"""
        if not description:
            description = f"{action.value} Google integration"
        
        return self.log(
            user_id=user_id,
            action=action,
            entity_type=AuditEntityType.GOOGLE_CREDENTIALS,
            description=description,
            success=success,
            error_message=error_message
        )
    
    def log_settings_operation(
        self,
        user_id: str,
        action: AuditAction,
        description: str = "",
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log settings-related operations"""
        if not description:
            description = f"{action.value} settings"
        
        return self.log(
            user_id=user_id,
            action=action,
            entity_type=AuditEntityType.SETTINGS,
            description=description,
            success=success,
            error_message=error_message
        )
    
    def log_error(
        self,
        user_id: str,
        entity_type: AuditEntityType,
        description: str,
        error_message: str,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log an error event"""
        return self.log(
            user_id=user_id,
            action=AuditAction.ERROR,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            details=details,
            success=False,
            error_message=error_message
        )


# Singleton instance
audit_service = AuditService()