"""
Database layer for LifeLog
"""

from .connection import get_db, init_db
from .user_crud import (
    get_user_by_email,
    get_user_by_username,
    get_user_by_id,
    create_user,
    update_user,
    delete_user,
    get_all_users,
)
from .memory_crud import (
    get_memory_by_id,
    get_memories_by_user,
    create_memory,
    update_memory,
    delete_memory,
)
from .google_crud import (
    get_google_credentials,
    save_google_credentials,
    delete_google_credentials,
)
from .action_crud import (
    create_proposed_action,
    get_proposed_action,
    get_proposed_actions,
    get_pending_actions,
    get_actions_requiring_approval,
    update_proposed_action,
    approve_action,
    reject_action,
    complete_action,
    delete_proposed_action,
    delete_actions_by_memory,
    get_action_count_by_status,
)
from .audit_crud import (
    create_audit_log,
    get_audit_log,
    get_audit_logs,
    get_audit_logs_by_user,
    get_recent_audit_logs,
    delete_audit_logs_by_user,
    delete_audit_logs_older_than,
    get_audit_stats,
)

__all__ = [
    "get_db",
    "init_db",
    "get_user_by_email",
    "get_user_by_username",
    "get_user_by_id",
    "create_user",
    "update_user",
    "delete_user",
    "get_all_users",
    "get_memory_by_id",
    "get_memories_by_user",
    "create_memory",
    "update_memory",
    "delete_memory",
    "get_google_credentials",
    "save_google_credentials",
    "delete_google_credentials",
    "create_proposed_action",
    "get_proposed_action",
    "get_proposed_actions",
    "get_pending_actions",
    "get_actions_requiring_approval",
    "update_proposed_action",
    "approve_action",
    "reject_action",
    "complete_action",
    "delete_proposed_action",
    "delete_actions_by_memory",
    "get_action_count_by_status",
    "create_audit_log",
    "get_audit_log",
    "get_audit_logs",
    "get_audit_logs_by_user",
    "get_recent_audit_logs",
    "delete_audit_logs_by_user",
    "delete_audit_logs_older_than",
    "get_audit_stats",
]
