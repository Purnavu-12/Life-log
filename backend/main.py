from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends, status, Query, Body, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="LifeLog API",
    description="Backend service for LifeLog - AI-powered memory management",
    version="0.1.0"
)

# Configure CORS
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:8000",
        "http://localhost:8006",
        "http://localhost:8007",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
        "http://127.0.0.1:3004",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8006",
        "http://127.0.0.1:8007",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
from database import init_db
init_db()

# Initialize services
from services.transcription import TranscriptionService
from services.extraction import ExtractionService
from services.search import SearchService
from services.auth import auth_service, get_current_user, get_current_active_user
from services.google import google_oauth_service
from services.poolside import poolside_service

# Security
security = HTTPBearer()

# ============================================================================
# Local-only mode: single user, no authentication required
# ============================================================================
LOCAL_USER_ID = os.getenv("LOCAL_USER_ID", "local-user")


@app.on_event("startup")
async def startup_event():
    """Start MCP servers on application startup so health checks report them as running"""
    try:
        from mcp import memory_mcp_server, calendar_mcp_server, gmail_mcp_server
        for server in [memory_mcp_server, calendar_mcp_server, gmail_mcp_server]:
            try:
                await server.start()
            except Exception as e:
                logger.error(f"Failed to start {getattr(server, 'config', None) and server.config.name} MCP server: {str(e)}")
    except Exception as e:
        logger.error(f"Could not start MCP servers on startup: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check Poolside API health
    poolside_health = await poolside_service.health_check()
    
    # Check MCP servers health
    mcp_health = await _get_mcp_health()
    
    return {
        "status": "healthy", 
        "service": "LifeLog API",
        "poolside": poolside_health,
        "mcp_servers": mcp_health,
        "environment": {
            "poolside_available": poolside_health.get("poolside_available", False),
            "openai_available": poolside_health.get("openai_available", False),
            "google_configured": bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"))
        }
    }


async def _get_mcp_health() -> Dict[str, Any]:
    """Get health status for all MCP servers (starts servers lazily if not running)"""
    from mcp import memory_mcp_server, calendar_mcp_server, gmail_mcp_server

    health = {}

    try:
        if not memory_mcp_server.running:
            await memory_mcp_server.start()
        health["memory"] = await memory_mcp_server.health_check()
    except Exception as e:
        health["memory"] = {"status": "error", "error": str(e)}
    
    try:
        if not calendar_mcp_server.running:
            await calendar_mcp_server.start()
        calendar_health = await calendar_mcp_server.health_check()
        health["calendar"] = calendar_health
    except Exception as e:
        health["calendar"] = {"status": "error", "error": str(e)}
    
    try:
        if not gmail_mcp_server.running:
            await gmail_mcp_server.start()
        gmail_health = await gmail_mcp_server.health_check()
        health["gmail"] = gmail_health
    except Exception as e:
        health["gmail"] = {"status": "error", "error": str(e)}
    
    return health


@app.get("/api/poolside/health")
async def poolside_health():
    """Check Poolside AI service health"""
    try:
        health = await poolside_service.health_check()
        return JSONResponse(
            status_code=200,
            content=health
        )
    except Exception as e:
        logger.error(f"Poolside health check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mcp/health")
async def mcp_health():
    """Check all MCP servers health"""
    try:
        health = await _get_mcp_health()
        return JSONResponse(
            status_code=200,
            content={"mcp_servers": health}
        )
    except Exception as e:
        logger.error(f"MCP health check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mcp/health/{server_name}")
async def mcp_server_health(server_name: str):
    """Check health of a specific MCP server"""
    try:
        from mcp import memory_mcp_server, calendar_mcp_server, gmail_mcp_server
        
        servers = {
            "memory": memory_mcp_server,
            "calendar": calendar_mcp_server,
            "gmail": gmail_mcp_server
        }
        
        if server_name not in servers:
            raise HTTPException(status_code=404, detail=f"MCP server '{server_name}' not found")
        
        health = await servers[server_name].health_check()
        return JSONResponse(
            status_code=200,
            content={"server": server_name, "health": health}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP server health check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Authentication Routes

from models.user import UserCreate, UserResponse
from models.token import Token, RefreshTokenRequest
from pydantic import BaseModel, model_validator


class LoginRequest(BaseModel):
    """Login request body model.

    Accepts either `email` (primary) or `username` (for local / installed-app
    logins where the identifier is a username) plus `password`.
    """
    email: Optional[str] = None
    username: Optional[str] = None
    password: str

    @model_validator(mode="after")
    def _ensure_identifier(self):
        if not self.email and not self.username:
            raise ValueError("either email or username must be provided")
        return self
from fastapi.encoders import jsonable_encoder

def get_local_user() -> UserResponse:
    """Return the single local user (authentication disabled for local use)"""
    from datetime import datetime
    return UserResponse(
        id=LOCAL_USER_ID,
        email="local@lifelog.ai",
        username="local",
        full_name="Local User",
        is_active=True,
        created_at=datetime.utcnow(),
        last_login=None,
    )


# Privacy Routes
# ============================================================================

@app.post("/api/privacy/clear-data")
async def clear_user_data(
    current_user: UserResponse = Depends(get_local_user)
):
    """Clear all user data (memories, actions, audit logs, google credentials)"""
    try:
        from database import (
            delete_audit_logs_by_user,
            delete_google_credentials,
            delete_proposed_action,
            delete_memory
        )
        
        user_id = current_user.id
        
        # Delete all memories for the user
        # First get all memories to delete associated actions
        from database import get_memories_by_user
        memories = get_memories_by_user(user_id, 1000, 0)
        
        # Delete all proposed actions for each memory
        actions_deleted = 0
        for memory in memories:
            from database import delete_actions_by_memory
            actions_deleted += delete_actions_by_memory(memory.id, user_id)
        
        # Delete all memories
        memories_deleted = 0
        for memory in memories:
            success = delete_memory(memory.id, user_id)
            if success:
                memories_deleted += 1
        
        # Delete all audit logs
        audit_deleted = delete_audit_logs_by_user(user_id)
        
        # Delete Google credentials
        google_deleted = delete_google_credentials(user_id)
        
        # Log the data deletion
        from services.audit import audit_service
        from models.audit import AuditAction, AuditEntityType
        
        audit_service.log(
            user_id=user_id,
            action=AuditAction.DELETE,
            entity_type=AuditEntityType.USER,
            description="Clear all user data - privacy request",
            details={
                "memories_deleted": memories_deleted,
                "actions_deleted": actions_deleted,
                "audit_logs_deleted": audit_deleted,
                "google_credentials_deleted": google_deleted
            },
            success=True
        )
        
        logger.info(f"Cleared all data for user: {user_id}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "All user data has been cleared",
                "details": {
                    "memories_deleted": memories_deleted,
                    "actions_deleted": actions_deleted,
                    "audit_logs_deleted": audit_deleted,
                    "google_credentials_deleted": google_deleted
                }
            }
        )
    except Exception as e:
        logger.error(f"Error clearing user data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/privacy/export-data")
async def export_user_data(
    current_user: UserResponse = Depends(get_local_user)
):
    """Export all user data as JSON"""
    try:
        from database import (
            get_memories_by_user,
            get_proposed_actions,
            get_audit_logs_by_user,
            get_google_credentials
        )
        
        user_id = current_user.id
        
        # Get all user data
        memories = get_memories_by_user(user_id, 1000, 0)
        actions = get_proposed_actions(user_id, 1000, 0)
        audit_logs = get_audit_logs_by_user(user_id, 1000)
        google_creds = get_google_credentials(user_id)
        
        # Format memories for export
        formatted_memories = []
        for mem in memories:
            formatted_memories.append({
                "id": mem.id,
                "content": mem.content,
                "summary": mem.summary,
                "tags": mem.tags or [],
                "sentiment": mem.sentiment,
                "people": mem.people or [],
                "tasks": mem.tasks or [],
                "topics": mem.topics or [],
                "dates": mem.dates or [],
                "action_items": mem.action_items or [],
                "filename": mem.filename,
                "source": mem.source,
                "timestamp": mem.timestamp.isoformat() if hasattr(mem.timestamp, "isoformat") else str(mem.timestamp)
            })
        
        # Format actions for export
        formatted_actions = []
        for action in actions:
            formatted_actions.append({
                "id": action.id,
                "title": action.title,
                "description": action.description,
                "action_type": action.action_type.value if hasattr(action.action_type, 'value') else str(action.action_type),
                "priority": action.priority.value if hasattr(action.priority, 'value') else str(action.priority),
                "status": action.status.value if hasattr(action.status, 'value') else str(action.status),
                "confidence": action.confidence,
                "memory_id": action.memory_id,
                "related_entities": action.related_entities,
                "scheduled_time": action.scheduled_time,
                "created_at": action.created_at.isoformat() if hasattr(action.created_at, "isoformat") else str(action.created_at)
            })
        
        # Format audit logs for export
        formatted_audit_logs = []
        for log in audit_logs:
            formatted_audit_logs.append({
                "id": log.id,
                "action": log.action.value if hasattr(log.action, 'value') else str(log.action),
                "entity_type": log.entity_type.value if hasattr(log.entity_type, 'value') else str(log.entity_type),
                "entity_id": log.entity_id,
                "description": log.description,
                "details": log.details,
                "success": log.success,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if hasattr(log.created_at, "isoformat") else str(log.created_at)
            })
        
        # Format google credentials for export (mask sensitive data)
        formatted_google_creds = None
        if google_creds:
            formatted_google_creds = {
                "google_user_id": google_creds.google_user_id,
                "email": google_creds.email,
                "scopes": google_creds.scopes,
                "connected_at": google_creds.expires_at.isoformat() if hasattr(google_creds.expires_at, "isoformat") else str(google_creds.expires_at)
            }
        
        # Create export data
        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "user_email": current_user.email,
            "data": {
                "memories": formatted_memories,
                "proposed_actions": formatted_actions,
                "audit_logs": formatted_audit_logs,
                "google_credentials": formatted_google_creds
            },
            "statistics": {
                "total_memories": len(formatted_memories),
                "total_actions": len(formatted_actions),
                "total_audit_logs": len(formatted_audit_logs),
                "google_connected": formatted_google_creds is not None
            }
        }
        
        # Log the export
        from services.audit import audit_service
        from models.audit import AuditAction, AuditEntityType
        
        audit_service.log(
            user_id=user_id,
            action=AuditAction.EXPORT,
            entity_type=AuditEntityType.USER,
            description="Export all user data - privacy request",
            details={
                "memories_count": len(formatted_memories),
                "actions_count": len(formatted_actions),
                "audit_logs_count": len(formatted_audit_logs),
                "google_connected": formatted_google_creds is not None
            },
            success=True
        )
        
        logger.info(f"Exported data for user: {user_id}")
        
        return JSONResponse(
            status_code=200,
            content=export_data
        )
    except Exception as e:
        logger.error(f"Error exporting user data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/privacy/revoke-google")
async def revoke_google_access(
    current_user: UserResponse = Depends(get_local_user)
):
    """Revoke Google OAuth access"""
    try:
        from database import delete_google_credentials
        from services.audit import audit_service
        from models.audit import AuditAction, AuditEntityType
        
        user_id = current_user.id
        
        # Delete Google credentials
        success = delete_google_credentials(user_id)
        
        # Log the revocation
        audit_service.log(
            user_id=user_id,
            action=AuditAction.DELETE,
            entity_type=AuditEntityType.GOOGLE_CREDENTIALS,
            description="Revoke Google OAuth access - privacy request",
            success=success
        )
        
        if success:
            logger.info(f"Revoked Google access for user: {user_id}")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Google access has been revoked"
                }
            )
        else:
            logger.info(f"No Google access to revoke for user: {user_id}")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "No Google access was connected"
                }
            )
    except Exception as e:
        logger.error(f"Error revoking Google access: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================

@app.post("/auth/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        user = auth_service.register_user(user_data)
        logger.info(f"Registered new user: {user.username}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/login", response_model=Token)
async def login_user(
    body: Optional[LoginRequest] = Body(None),
    email: Optional[str] = Query(None),
    password: Optional[str] = Query(None),
):
    """Login and get JWT token (accepts JSON body or query params)"""
    try:
        # Support JSON body (used by the frontend) and query params for backwards compat
        if body is not None:
            email = body.email
            password = body.password
            username = body.username
        else:
            username = None

        if not password:
            raise HTTPException(
                status_code=422,
                detail="password is required (send JSON body or query params)"
            )

        # Authenticate by email (preferred) or username (local/installed-app logins).
        user = None
        if email:
            user = auth_service.authenticate_user(email, password)
        elif username:
            user = auth_service.authenticate_user_by_username(username, password)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email, username, or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Create tokens
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "email": user.email
        }
        
        access_token = auth_service.create_access_token(token_data)
        refresh_token = auth_service.create_refresh_token(token_data)
        
        logger.info(f"User logged in: {user.username}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60,  # 30 minutes
            "user": jsonable_encoder(user)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/refresh", response_model=Token)
async def refresh_token(
    body: Optional[RefreshTokenRequest] = Body(None),
    refresh_token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Refresh access token using refresh token (accepts JSON body, query param, or Authorization header)"""
    try:
        # Support JSON body (frontend), query param, or Authorization: Bearer header
        if body is not None and body.refresh_token:
            refresh_token = body.refresh_token
        elif not refresh_token and authorization and authorization.lower().startswith("bearer "):
            refresh_token = authorization[7:].strip()

        if not refresh_token:
            raise HTTPException(
                status_code=422,
                detail="refresh_token is required (send JSON body, query param, or Authorization header)"
            )

        tokens = auth_service.refresh_access_token(refresh_token)
        logger.info("Access token refreshed")
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_profile(current_user: UserResponse = Depends(get_local_user)):
    """Get current user profile"""
    return current_user


# ============================================================================
# User Settings Routes
# ============================================================================

@app.get("/api/settings")
async def get_user_settings(current_user: UserResponse = Depends(get_local_user)):
    """Get current user settings"""
    from database.connection import get_db
    default = {
        "email_notifications": True,
        "auto_create_events": True,
        "theme": "dark",
        "google_calendar_enabled": False,
        "gmail_enabled": False,
    }
    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT email_notifications, auto_create_events, theme, google_calendar_enabled, gmail_enabled "
                "FROM user_settings WHERE user_id = ?",
                (current_user.id,)
            ).fetchone()
        if not row:
            return {**default}
        return {
            "email_notifications": bool(row["email_notifications"]),
            "auto_create_events": bool(row["auto_create_events"]),
            "theme": row["theme"] or "dark",
            "google_calendar_enabled": bool(row["google_calendar_enabled"]),
            "gmail_enabled": bool(row["gmail_enabled"]),
        }
    except Exception as e:
        logger.error(f"Error fetching settings: {str(e)}")
        return {**default}


@app.put("/api/settings")
async def update_user_settings(
    payload: dict = Body(...),
    current_user: UserResponse = Depends(get_local_user)
):
    """Update current user settings"""
    from database.connection import get_db
    try:
        allowed = {
            "email_notifications": payload.get("email_notifications", True),
            "auto_create_events": payload.get("auto_create_events", True),
            "theme": payload.get("theme", "dark"),
            "google_calendar_enabled": payload.get("google_calendar_enabled", False),
            "gmail_enabled": payload.get("gmail_enabled", False),
        }
        with get_db() as conn:
            # Upsert settings
            conn.execute(
                """
                INSERT INTO user_settings (user_id, email_notifications, auto_create_events, theme, google_calendar_enabled, gmail_enabled)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    email_notifications = excluded.email_notifications,
                    auto_create_events = excluded.auto_create_events,
                    theme = excluded.theme,
                    google_calendar_enabled = excluded.google_calendar_enabled,
                    gmail_enabled = excluded.gmail_enabled
                """,
                (
                    current_user.id,
                    int(bool(allowed["email_notifications"])),
                    int(bool(allowed["auto_create_events"])),
                    allowed["theme"],
                    int(bool(allowed["google_calendar_enabled"])),
                    int(bool(allowed["gmail_enabled"])),
                )
            )
            conn.commit()

        from services.audit import audit_service
        from models.audit import AuditAction, AuditEntityType
        audit_service.log(
            user_id=current_user.id,
            action=AuditAction.UPDATE,
            entity_type=AuditEntityType.USER,
            description="Updated user settings",
            details={},
            success=True
        )

        return {
            "success": True,
            "email_notifications": allowed["email_notifications"],
            "auto_create_events": allowed["auto_create_events"],
            "theme": allowed["theme"],
            "google_calendar_enabled": allowed["google_calendar_enabled"],
            "gmail_enabled": allowed["gmail_enabled"],
        }
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Google OAuth Routes
# ============================================================================

from models.google import GoogleCredentials

@app.get("/auth/google")
async def google_login(request: Request):
    """Redirect to Google OAuth consent screen"""
    try:
        # Get state parameter for CSRF protection
        state = request.query_params.get("state", "")
        scopes = request.query_params.getlist("scope")
        
        # Determine scopes based on what user wants to connect
        if "gmail" in scopes:
            auth_url = google_oauth_service.get_authorization_url(
                state=state,
                scopes=["https://www.googleapis.com/auth/gmail.readonly"]
            )
        elif "calendar" in scopes:
            auth_url = google_oauth_service.get_authorization_url(
                state=state,
                scopes=["https://www.googleapis.com/auth/calendar"]
            )
        else:
            # Default: both
            auth_url = google_oauth_service.get_authorization_url(state=state)
        
        logger.info(f"Redirecting to Google OAuth: {auth_url}")
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/google/callback")
async def google_callback(request: Request, code: str, state: str = None):
    """Google OAuth callback handler"""
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    try:
        # Exchange code for token (with PKCE state)
        credentials = await google_oauth_service.exchange_code_for_token(code, state)
        
        # Associate with local user for development
        # In production, extract user_id from state parameter
        user_id = LOCAL_USER_ID
        
        # Save credentials to database
        credentials.user_id = user_id
        saved_creds = google_oauth_service.save_credentials(credentials, user_id)
        
        logger.info(f"Google OAuth callback successful for user {user_id}: {credentials.email}")
        
        # Redirect back to the frontend with success status
        from urllib.parse import urlencode, quote
        query = urlencode({"google": "connected", "email": credentials.email or ""})
        return RedirectResponse(url=f"{frontend_url}/settings?{query}")
    except Exception as e:
        logger.error(f"Google OAuth callback error: {str(e)}")
        from urllib.parse import quote
        return RedirectResponse(url=f"{frontend_url}/settings?google=error&message={quote(str(e))}")


@app.post("/auth/google/connect")
async def connect_google_credentials(
    access_token: str,
    refresh_token: Optional[str] = None,
    google_user_id: str = None,
    email: str = None,
    scopes: List[str] = None,
    current_user: UserResponse = Depends(get_local_user)
):
    """Connect Google credentials to user account"""
    try:
        from datetime import datetime, timedelta
        
        credentials = GoogleCredentials(
            user_id=current_user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_at=datetime.utcnow() + timedelta(seconds=3600),  # 1 hour
            scopes=scopes or [],
            google_user_id=google_user_id,
            email=email
        )
        
        saved_creds = google_oauth_service.save_credentials(credentials, current_user.id)
        logger.info(f"Connected Google account for user: {current_user.id}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Google account connected successfully",
                "email": email
            }
        )
    except Exception as e:
        logger.error(f"Error connecting Google: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/google/status")
async def get_google_status(current_user: UserResponse = Depends(get_local_user)):
    """Check if user has Google connected"""
    try:
        credentials = google_oauth_service.get_credentials(current_user.id)
        if credentials:
            return {
                "connected": True,
                "email": credentials.email,
                "scopes": credentials.scopes
            }
        return {"connected": False}
    except Exception as e:
        logger.error(f"Error checking Google status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/google/disconnect")
async def disconnect_google(current_user: UserResponse = Depends(get_local_user)):
    """Disconnect Google account"""
    try:
        success = google_oauth_service.delete_credentials(current_user.id)
        if success:
            logger.info(f"Disconnected Google account for user: {current_user.id}")
            return JSONResponse(
                status_code=200,
                content={"success": True, "message": "Google account disconnected"}
            )
        else:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "No Google account was connected"}
            )
    except Exception as e:
        logger.error(f"Error disconnecting Google: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Google Calendar API Routes
# ============================================================================

from services.google import get_calendar_service, get_gmail_service

@app.get("/api/google/calendars")
async def list_calendars(current_user: UserResponse = Depends(get_local_user)):
    """List all Google calendars for the user"""
    try:
        calendar_service = get_calendar_service(current_user.id)
        calendars = await calendar_service.list_calendars()
        return {"calendars": calendars}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing calendars: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/google/events")
async def list_events(
    calendar_id: str = "primary",
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    current_user: UserResponse = Depends(get_local_user)
):
    """List events from a Google calendar"""
    try:
        calendar_service = get_calendar_service(current_user.id)
        events = await calendar_service.list_events(calendar_id, time_min, time_max)
        return {"events": events}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/google/events")
async def create_event(
    summary: str,
    start: str,
    end: str,
    description: Optional[str] = None,
    location: Optional[str] = None,
    calendar_id: str = "primary",
    current_user: UserResponse = Depends(get_local_user)
):
    """Create a new Google Calendar event"""
    try:
        calendar_service = get_calendar_service(current_user.id)
        event = await calendar_service.create_event(
            summary=summary,
            start=start,
            end=end,
            description=description,
            location=location,
            calendar_id=calendar_id
        )
        return {"success": True, "event": event}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/google/events/{event_id}")
async def delete_event(
    event_id: str,
    calendar_id: str = "primary",
    current_user: UserResponse = Depends(get_local_user)
):
    """Delete a Google Calendar event"""
    try:
        calendar_service = get_calendar_service(current_user.id)
        success = await calendar_service.delete_event(calendar_id, event_id)
        return {"success": success}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/google/freebusy")
async def freebusy(
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    current_user: UserResponse = Depends(get_local_user)
):
    """Query free/busy slots from Google Calendar"""
    try:
        calendar_service = get_calendar_service(current_user.id)
        result = await calendar_service.freebusy(time_min, time_max)
        return {"freebusy": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching free/busy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Google Gmail API Routes
# ============================================================================

@app.get("/api/google/messages")
async def list_messages(
    query: Optional[str] = None,
    max_results: int = 10,
    current_user: UserResponse = Depends(get_local_user)
):
    """List messages from Gmail"""
    try:
        gmail_service = get_gmail_service(current_user.id)
        messages = await gmail_service.list_messages(query, max_results)
        return {"messages": messages}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/google/messages/{message_id}")
async def get_message(
    message_id: str,
    current_user: UserResponse = Depends(get_local_user)
):
    """Get a specific Gmail message"""
    try:
        gmail_service = get_gmail_service(current_user.id)
        message = await gmail_service.get_message(message_id)
        return {"message": message}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/google/messages/important")
async def list_important_messages(
    max_results: int = 10,
    current_user: UserResponse = Depends(get_local_user)
):
    """List important unread messages from Gmail"""
    try:
        gmail_service = get_gmail_service(current_user.id)
        messages = await gmail_service.list_important(max_results)
        return {"messages": messages}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing important messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/google/profile")
async def get_gmail_profile(current_user: UserResponse = Depends(get_local_user)):
    """Get Gmail profile"""
    try:
        gmail_service = get_gmail_service(current_user.id)
        profile = await gmail_service.get_profile()
        return {"profile": profile}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Gmail profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/google/index-emails")
async def index_emails(
    limit: int = 50,
    current_user: UserResponse = Depends(get_local_user)
):
    """Index recent emails for search"""
    try:
        gmail_service = get_gmail_service(current_user.id)
        emails = await gmail_service.index_emails(limit)
        return {"emails": emails, "count": len(emails)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error indexing emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Audit Log Routes
# ============================================================================

from models.audit import AuditLogCreate, AuditLogResponse, AuditAction, AuditEntityType

@app.post("/api/audit/logs", response_model=AuditLogResponse)
async def create_audit_log(
    log_data: AuditLogCreate,
    current_user: UserResponse = Depends(get_local_user)
):
    """Create a new audit log entry"""
    try:
        # Ensure the user_id matches the current user
        if log_data.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot create audit log for another user")
        
        from database import create_audit_log
        
        audit_log = create_audit_log(log_data)
        logger.info(f"Created audit log: {audit_log.id}")
        
        return audit_log
    except Exception as e:
        logger.error(f"Error creating audit log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit/logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    action: Optional[AuditAction] = None,
    entity_type: Optional[AuditEntityType] = None,
    entity_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: UserResponse = Depends(get_local_user)
):
    """List audit logs with optional filters"""
    try:
        from database import get_audit_logs
        
        # Only allow users to see their own audit logs (admins can see all)
        logs = get_audit_logs(
            user_id=current_user.id,  # Only current user's logs
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"Fetched {len(logs)} audit logs for user: {current_user.id}")
        return logs
    except Exception as e:
        logger.error(f"Error listing audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    current_user: UserResponse = Depends(get_local_user)
):
    """Get a specific audit log"""
    try:
        from database import get_audit_log
        
        audit_log = get_audit_log(log_id)
        if not audit_log:
            raise HTTPException(status_code=404, detail="Audit log not found")
        
        # Ensure the user can only see their own audit logs
        if audit_log.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this audit log")
        
        return audit_log
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching audit log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/audit/logs")
async def delete_user_audit_logs(
    current_user: UserResponse = Depends(get_local_user)
):
    """Delete all audit logs for the current user (for privacy)"""
    try:
        from database import delete_audit_logs_by_user
        
        count = delete_audit_logs_by_user(current_user.id)
        logger.info(f"Deleted {count} audit logs for user: {current_user.id}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Deleted {count} audit logs",
                "deleted_count": count
            }
        )
    except Exception as e:
        logger.error(f"Error deleting audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit/stats")
async def get_audit_stats(
    current_user: UserResponse = Depends(get_local_user)
):
    """Get audit statistics"""
    try:
        from database import get_audit_logs_by_user
        
        # Get logs for current user only
        logs = get_audit_logs_by_user(current_user.id, 1000)
        
        # Calculate stats
        stats = {
            "total_logs": len(logs),
            "by_action": {},
            "by_entity_type": {},
            "by_success": {"success": 0, "failed": 0},
            "recent_errors": []
        }
        
        for log in logs:
            # Count by action
            action = log.action.value if hasattr(log.action, 'value') else str(log.action)
            stats["by_action"][action] = stats["by_action"].get(action, 0) + 1
            
            # Count by entity type
            entity_type = log.entity_type.value if hasattr(log.entity_type, 'value') else str(log.entity_type)
            stats["by_entity_type"][entity_type] = stats["by_entity_type"].get(entity_type, 0) + 1
            
            # Count by success
            key = "success" if log.success else "failed"
            stats["by_success"][key] = stats["by_success"].get(key, 0) + 1
            
            # Collect recent errors
            if not log.success and log.error_message:
                stats["recent_errors"].append({
                    "description": log.description,
                    "error_message": log.error_message,
                    "created_at": log.created_at,
                    "action": action,
                    "entity_type": entity_type
                })
        
        # Limit recent errors to 5
        stats["recent_errors"] = stats["recent_errors"][:5]
        
        logger.info(f"Generated audit stats for user: {current_user.id}")
        return JSONResponse(status_code=200, content=stats)
    except Exception as e:
        logger.error(f"Error generating audit stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MCP Tool Routes
# ============================================================================

@app.post("/api/mcp/tools")
async def list_mcp_tools():
    """List all available MCP tools across all servers"""
    try:
        from mcp import memory_mcp_server, calendar_mcp_server, gmail_mcp_server
        
        servers = [memory_mcp_server, calendar_mcp_server, gmail_mcp_server]
        
        all_tools = []
        for server in servers:
            try:
                tools = await server.list_tools()
                for tool in tools:
                    tool["server"] = server.config.name
                all_tools.extend(tools)
            except Exception as e:
                logger.error(f"Error listing tools for server {server.config.name}: {str(e)}")
        
        return JSONResponse(
            status_code=200,
            content={"tools": all_tools, "count": len(all_tools)}
        )
    except Exception as e:
        logger.error(f"Error listing MCP tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mcp/tools/{server_name}/{tool_name}")
async def call_mcp_tool(
    server_name: str,
    tool_name: str,
    arguments: Dict[str, Any],
    current_user: UserResponse = Depends(get_local_user)
):
    """Call a specific MCP tool"""
    try:
        from mcp import memory_mcp_server, calendar_mcp_server, gmail_mcp_server
        
        servers = {
            "memory": memory_mcp_server,
            "lifelog-memory": memory_mcp_server,
            "calendar": calendar_mcp_server,
            "lifelog-calendar": calendar_mcp_server,
            "gmail": gmail_mcp_server,
            "lifelog-gmail": gmail_mcp_server
        }
        
        if server_name not in servers:
            raise HTTPException(status_code=404, detail=f"MCP server '{server_name}' not found")
        
        server = servers[server_name]
        # Update server with current user context
        if hasattr(server, 'user_id'):
            server.user_id = current_user.id
        
        result = await server.call_tool(tool_name, arguments)
        
        return JSONResponse(
            status_code=200,
            content=result
        )
    except Exception as e:
        logger.error(f"Error calling MCP tool: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Proposed Actions Routes
# ============================================================================

from models.action import (
    ProposedActionCreate, 
    ProposedActionResponse, 
    ActionApprovalRequest,
    ActionCompletionRequest,
    ActionStatus,
    ActionType,
    ActionPriority
)

@app.post("/api/actions", response_model=ProposedActionResponse)
async def create_action(
    action_data: ProposedActionCreate,
    current_user: UserResponse = Depends(get_local_user)
):
    """Create a new proposed action"""
    try:
        from database import create_proposed_action
        
        action = create_proposed_action(action_data, current_user.id)
        logger.info(f"Created action: {action.id} for user: {current_user.id}")
        
        return action
    except Exception as e:
        logger.error(f"Error creating action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/actions", response_model=List[ProposedActionResponse])
async def list_actions(
    status: Optional[ActionStatus] = None,
    action_type: Optional[ActionType] = None,
    priority: Optional[ActionPriority] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: UserResponse = Depends(get_local_user)
):
    """List proposed actions with optional filters"""
    try:
        from database import get_proposed_actions
        
        actions = get_proposed_actions(
            user_id=current_user.id,
            status=status,
            action_type=action_type,
            priority=priority,
            limit=limit,
            offset=offset
        )
        logger.info(f"Fetched {len(actions)} actions for user: {current_user.id}")
        
        return actions
    except Exception as e:
        logger.error(f"Error listing actions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/actions/pending", response_model=List[ProposedActionResponse])
async def list_pending_actions(
    limit: int = 20,
    current_user: UserResponse = Depends(get_local_user)
):
    """List pending actions that require approval"""
    try:
        from database import get_pending_actions
        
        actions = get_pending_actions(current_user.id, limit)
        logger.info(f"Fetched {len(actions)} pending actions for user: {current_user.id}")
        
        return actions
    except Exception as e:
        logger.error(f"Error fetching pending actions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/actions/queue", response_model=List[ProposedActionResponse])
async def get_approval_queue(
    limit: int = 20,
    current_user: UserResponse = Depends(get_local_user)
):
    """Get actions approval queue (same as pending for now)"""
    return await list_pending_actions(limit, current_user)


@app.get("/api/actions/counts")
async def get_action_counts(
    current_user: UserResponse = Depends(get_local_user)
):
    """Get count of actions by status"""
    try:
        from database import get_action_count_by_status
        
        counts = get_action_count_by_status(current_user.id)
        logger.info(f"Fetched action counts for user: {current_user.id}")
        
        return {"counts": counts}
    except Exception as e:
        logger.error(f"Error fetching action counts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/actions/{action_id}", response_model=ProposedActionResponse)
async def get_action(
    action_id: str,
    current_user: UserResponse = Depends(get_local_user)
):
    """Get a specific proposed action"""
    try:
        from database import get_proposed_action
        
        action = get_proposed_action(action_id, current_user.id)
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        
        return action
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/actions/{action_id}", response_model=ProposedActionResponse)
async def update_action(
    action_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[ActionStatus] = None,
    priority: Optional[ActionPriority] = None,
    scheduled_time: Optional[str] = None,
    location: Optional[str] = None,
    recipients: Optional[List[str]] = None,
    current_user: UserResponse = Depends(get_local_user)
):
    """Update a proposed action"""
    try:
        from database import update_proposed_action
        
        action = update_proposed_action(
            action_id=action_id,
            user_id=current_user.id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            scheduled_time=scheduled_time,
            location=location,
            recipients=recipients
        )
        
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        
        logger.info(f"Updated action: {action_id}")
        return action
    except Exception as e:
        logger.error(f"Error updating action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/actions/{action_id}/approve", response_model=ProposedActionResponse)
async def approve_action_endpoint(
    action_id: str,
    request: ActionApprovalRequest,
    current_user: UserResponse = Depends(get_local_user)
):
    """Approve a proposed action.

    For calendar-type actions, this additionally creates the event in the
    user's Google Calendar (if connected), closing the confirmation loop:
    proposed -> approved -> event created. The DB status is updated first so
    the action is durable even if the calendar write fails (the failure is
    logged but does not roll back approval).
    """
    try:
        from database import approve_action

        action = approve_action(
            action_id=action_id,
            user_id=current_user.id,
            scheduled_time=request.scheduled_time
        )

        if not action:
            raise HTTPException(status_code=404, detail="Action not found")

        # Phase 13 of the build plan: after user confirmation, actually create
        # the calendar event (the safest workflow — never auto-create, only on approval).
        created_event_id = None
        if action.action_type in (ActionType.CREATE_EVENT, ActionType.SET_REMINDER):
            try:
                from database import is_google_connected
                # Don't attempt a calendar write (which can block on token refresh) if
                # the user hasn't connected Google. Approval is already persisted.
                if not is_google_connected(current_user.id):
                    logger.warning(f"Approved action {action_id} is a calendar action but Google is not connected; skipping event creation")
                else:
                    from services.google import get_calendar_service
                    calendar_service = get_calendar_service(current_user.id)
                    start_time = (action.scheduled_time or request.scheduled_time)
                    if start_time:
                        from datetime import datetime, timedelta
                        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                        duration = action.duration_minutes or 30
                        end_dt = start_dt + timedelta(minutes=duration)

                        # Run the (possibly synchronous) Google API call in a thread with
                        # a timeout so it can never hang the approval request.
                        async def _make_event():
                            return await asyncio.wait_for(
                                calendar_service.create_event(
                                    summary=action.title,
                                    start=start_dt.isoformat(),
                                    end=end_dt.isoformat(),
                                    description=action.description or f"Created from approved LifeLog action {action.id}",
                                    location=action.location,
                                ),
                                timeout=25,
                            )

                        event = await _make_event()
                        created_event_id = event.get("id") or event.get("htmlLink")
                        logger.info(f"Created Google Calendar event for approved action {action_id}: {created_event_id}")
                    else:
                        logger.warning(f"Approved action {action_id} has no scheduled_time; calendar event not created")
            except asyncio.TimeoutError:
                logger.warning(f"Approved action {action_id} but Google Calendar event creation timed out (approval still persisted)")
            except Exception as e:
                # Approval already persisted; calendar write is best-effort.
                logger.warning(f"Approved action {action_id} but Google Calendar event creation failed: {e}")

        logger.info(f"Approved action: {action_id} (calendar_event_id={created_event_id})")

        # Persist the created Google Calendar event id (best-effort) for auditability.
        if created_event_id:
            try:
                from database import get_db as _get_db
                with _get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE proposed_actions SET calendar_event_id = ? WHERE id = ? AND user_id = ?",
                        (created_event_id, action_id, current_user.id),
                    )
            except Exception as e:
                logger.warning(f"Could not persist calendar_event_id for action {action_id}: {e}")

        return action
    except Exception as e:
        logger.error(f"Error approving action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/actions/{action_id}/reject", response_model=ProposedActionResponse)
async def reject_action_endpoint(
    action_id: str,
    request: ActionApprovalRequest,
    current_user: UserResponse = Depends(get_local_user)
):
    """Reject a proposed action"""
    try:
        from database import reject_action
        
        action = reject_action(
            action_id=action_id,
            user_id=current_user.id,
            rejection_reason=request.rejection_reason
        )
        
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        
        logger.info(f"Rejected action: {action_id} with reason: {request.rejection_reason}")
        return action
    except Exception as e:
        logger.error(f"Error rejecting action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/actions/{action_id}/complete", response_model=ProposedActionResponse)
async def complete_action_endpoint(
    action_id: str,
    request: ActionCompletionRequest,
    current_user: UserResponse = Depends(get_local_user)
):
    """Mark a proposed action as completed"""
    try:
        from database import complete_action
        
        action = complete_action(
            action_id=action_id,
            user_id=current_user.id,
            notes=request.notes
        )
        
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        
        logger.info(f"Completed action: {action_id}")
        return action
    except Exception as e:
        logger.error(f"Error completing action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/actions/{action_id}")
async def delete_action(
    action_id: str,
    current_user: UserResponse = Depends(get_local_user)
):
    """Delete a proposed action"""
    try:
        from database import delete_proposed_action
        
        success = delete_proposed_action(action_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Action not found")
        
        logger.info(f"Deleted action: {action_id}")
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Action deleted successfully"}
        )
    except Exception as e:
        logger.error(f"Error deleting action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Dashboard Summary Routes
# ============================================================================

@app.get("/api/dashboard/summary")
async def get_dashboard_summary(
    current_user: UserResponse = Depends(get_local_user)
):
    """Get dashboard summary with key metrics and insights"""
    try:
        from database import get_memories_by_user, get_action_count_by_status, get_google_credentials
        
        # Get memory count and recent memories
        memories = get_memories_by_user(current_user.id, 5, 0)
        
        # Get action counts
        action_counts = get_action_count_by_status(current_user.id)
        
        # Get google connection status
        google_creds = get_google_credentials(current_user.id)
        google_connected = google_creds is not None
        
        # Get total memory count
        total_memories = len(get_memories_by_user(current_user.id, 1000, 0))
        
        # Analyze recent memories
        recent_memories = []
        for mem in memories:
            recent_memories.append({
                "id": mem.id,
                "date": mem.timestamp.isoformat() if hasattr(mem.timestamp, "isoformat") else str(mem.timestamp),
                "summary": mem.summary,
                "tags": mem.tags or [],
                "sentiment": mem.sentiment,
                "source": mem.source
            })
        
        # Count by sentiment
        sentiment_counts = {}
        for mem in get_memories_by_user(current_user.id, 1000, 0):
            sentiment = mem.sentiment or "neutral"
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Count by source
        source_counts = {}
        for mem in get_memories_by_user(current_user.id, 1000, 0):
            source = mem.source or "unknown"
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Collect all tags
        all_tags = []
        for mem in get_memories_by_user(current_user.id, 1000, 0):
            all_tags.extend(mem.tags or [])
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        summary = {
            "metrics": {
                "total_memories": total_memories,
                "recent_memories_count": len(recent_memories),
                "pending_actions": action_counts.get("pending", 0),
                "approved_actions": action_counts.get("approved", 0),
                "completed_actions": action_counts.get("completed", 0),
                "rejected_actions": action_counts.get("rejected", 0),
                "google_connected": google_connected,
                "google_email": google_creds.email if google_creds else None
            },
            "sentiment_distribution": sentiment_counts,
            "source_distribution": source_counts,
            "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "recent_memories": recent_memories,
            "total_tags": len(set(all_tags)),
            "unique_tags": len(set(all_tags))
        }
        
        logger.info(f"Generated dashboard summary for user: {current_user.id}")
        return JSONResponse(status_code=200, content=summary)
    except Exception as e:
        logger.error(f"Error generating dashboard summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/daily-briefing")
async def get_daily_briefing(
    current_user: UserResponse = Depends(get_local_user)
):
    """Get daily briefing with key information for the user"""
    try:
        from database import get_memories_by_user, get_pending_actions
        from services.google import get_calendar_service, get_gmail_service
        from datetime import datetime, timedelta
        
        # Get today's memories
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_memories = [
            mem for mem in get_memories_by_user(current_user.id, 50, 0)
            if hasattr(mem, 'timestamp') and mem.timestamp and 
            datetime.fromisoformat(str(mem.timestamp).replace('Z', '+00:00')) >= today_start
        ]
        
        # Get pending actions
        pending_actions = get_pending_actions(current_user.id, 5)
        
        # Get today's calendar events
        calendar_events = []
        gmail_messages = []
        
        try:
            # Check if Google Calendar is connected
            calendar_service = get_calendar_service(current_user.id)
            today_iso = datetime.utcnow().isoformat() + "Z"
            tomorrow_iso = (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"
            
            events = await calendar_service.list_events("primary", today_iso, tomorrow_iso)
            calendar_events = [
                {
                    "id": event.get("id"),
                    "summary": event.get("summary", "Untitled Event"),
                    "start": event.get("start", {}).get("dateTime", ""),
                    "end": event.get("end", {}).get("dateTime", ""),
                    "location": event.get("location")
                }
                for event in events
            ]
        except Exception as e:
            logger.warning(f"Could not fetch calendar events: {str(e)}")
            calendar_events = []
        
        try:
            # Check if Gmail is connected
            gmail_service = get_gmail_service(current_user.id)
            messages = await gmail_service.list_important(5)
            gmail_messages = [
                {
                    "id": msg.get("id"),
                    "subject": _extract_subject_from_message(msg),
                    "from": _extract_sender_from_message(msg),
                    "snippet": msg.get("snippet", "")[:100] + "..."
                }
                for msg in messages
            ]
        except Exception as e:
            logger.warning(f"Could not fetch Gmail messages: {str(e)}")
            gmail_messages = []
        
        briefing = {
            "date": datetime.utcnow().isoformat(),
            "memories": {
                "today_count": len(today_memories),
                "recent": [
                    {
                        "id": mem.id,
                        "summary": mem.summary,
                        "tags": mem.tags or [],
                        "sentiment": mem.sentiment
                    }
                    for mem in today_memories[:3]
                ]
            },
            "actions": {
                "pending_count": len(pending_actions),
                "high_priority": [
                    {
                        "id": action.id,
                        "title": action.title,
                        "priority": action.priority,
                        "action_type": action.action_type
                    }
                    for action in pending_actions
                    if action.priority == "high" or action.priority == "urgent"
                ]
            },
            "calendar": {
                "today_events_count": len(calendar_events),
                "upcoming": calendar_events
            },
            "gmail": {
                "important_messages_count": len(gmail_messages),
                "messages": gmail_messages
            },
            "quick_stats": {
                "total_memories": len(get_memories_by_user(current_user.id, 1000, 0)),
                "total_pending_actions": len(pending_actions)
            }
        }
        
        logger.info(f"Generated daily briefing for user: {current_user.id}")
        return JSONResponse(status_code=200, content=briefing)
    except Exception as e:
        logger.error(f"Error generating daily briefing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _extract_subject_from_message(message: Dict[str, Any]) -> str:
    """Extract subject from message"""
    try:
        headers = message.get('payload', {}).get('headers', [])
        for header in headers:
            if header.get('name', '').lower() == 'subject':
                return header.get('value', '(No Subject)')
        return '(No Subject)'
    except:
        return '(No Subject)'


def _extract_sender_from_message(message: Dict[str, Any]) -> str:
    """Extract sender from message"""
    try:
        headers = message.get('payload', {}).get('headers', [])
        for header in headers:
            if header.get('name', '').lower() == 'from':
                return header.get('value', 'Unknown')
        return 'Unknown'
    except:
        return 'Unknown'


# ============================================================================
# Memory Management Routes
# ============================================================================

@app.post("/api/upload")
async def upload_audio(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_local_user)
):
    """
    Upload audio file for processing
    - Transcribe using Whisper
    - Extract information using LLM
    - Store in vector database
    """
    try:
        # Check content type or file extension
        ALLOWED_AUDIO_TYPES = ["audio/", ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"]
        is_audio_by_content_type = file.content_type.startswith("audio/") if file.content_type else False
        is_audio_by_extension = any(file.filename.lower().endswith(ext) for ext in [".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"])
        
        logger.info(f"File upload: filename={file.filename}, content_type={file.content_type}, by_extension={is_audio_by_extension}, by_content_type={is_audio_by_content_type}")
        
        if not (is_audio_by_content_type or is_audio_by_extension):
            raise HTTPException(status_code=400, detail="File must be an audio file (mp3, wav, m4a, aac, ogg, flac)")

        logger.info(f"Processing audio for user {current_user.id}: {file.filename}")

        # Read file content
        contents = await file.read()

        # Initialize services with user context
        transcription_service = TranscriptionService(user_id=current_user.id)
        extraction_service = ExtractionService(user_id=current_user.id)
        search_service = SearchService(user_id=current_user.id)

        # Step 1: Transcribe
        try:
            transcript = await transcription_service.transcribe(contents)
            logger.info(f"Transcribed audio: {len(transcript)} characters")
            if not transcript or not transcript.strip():
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Transcription returned empty — the audio appears to contain no "
                        "recognizable speech. Make sure the recording has clear speech."
                    ),
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            # 422 (not 500) so the frontend can show a clear, actionable message
            # rather than a generic "Failed to fetch".
            raise HTTPException(
                status_code=422,
                detail=(
                    "Transcription failed. None of the configured transcription "
                    f"providers succeeded: {e}. Configure a working provider "
                    "(local whisper.cpp via SPECTRE_WHISPER_EXE, a valid "
                    "OPENAI_API_KEY, or Poolside audio support)."
                ),
            )

        # Step 2: Extract structured information (single LLM pass, no DB writes yet)
        extracted = await extraction_service.extract(transcript)
        logger.info(f"Extracted information: {extracted}")

        # Step 3: Store in vector database
        memory_id = await search_service.store_memory(
            content=transcript,
            extracted_data=extracted,
            filename=file.filename
        )
        logger.info(f"Stored memory: {memory_id} for user: {current_user.id}")

        # Step 4: Generate and save proposed actions ONCE, with the real memory_id
        proposed_actions = []
        try:
            generated_actions = await extraction_service.generate_proposed_actions(
                transcript=transcript,
                extracted_data=extracted,
                memory_id=memory_id
            )
            from database import create_proposed_action
            for action_create in generated_actions:
                try:
                    proposed_actions.append(create_proposed_action(action_create, current_user.id))
                except Exception as e:
                    logger.error(f"Failed to save proposed action: {str(e)}")
            logger.info(f"Generated and saved {len(proposed_actions)} proposed actions with memory_id: {memory_id}")
        except Exception as e:
            logger.warning(f"Could not generate proposed actions: {str(e)}")
            proposed_actions = []

        # Step 5: Save to SQL database
        from database import create_memory
        from models.memory import MemoryCreate
        
        memory_data = MemoryCreate(
            content=transcript,
            summary=extracted.get("summary"),
            sentiment=extracted.get("sentiment"),
            tags=extracted.get("tags", []),
            topics=extracted.get("topics", []),
            tasks=extracted.get("tasks", []),
            people=extracted.get("people", []),
            dates=extracted.get("dates", []),
            action_items=extracted.get("action_items", []),
            filename=file.filename,
            source="audio"
        )
        
        db_memory = create_memory(memory_data, current_user.id)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "memory_id": memory_id,
                "database_id": db_memory.id,
                "transcript": transcript,
                "extracted": extracted,
                "proposed_actions": [
                    {
                        "id": action.id,
                        "title": action.title,
                        "description": action.description,
                        "action_type": action.action_type.value,
                        "priority": action.priority.value,
                        "status": action.status.value,
                        "confidence": action.confidence
                    } if hasattr(action, 'id') else action
                    for action in proposed_actions
                ] if proposed_actions else [],
                "action_count": len(proposed_actions) if proposed_actions else 0
            }
        )
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search_memories(
    query: str,
    threshold: float = 0.5,
    current_user: UserResponse = Depends(get_local_user)
):
    """
    Search memories using semantic search
    """
    try:
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        logger.info(f"Searching for user {current_user.id}: {query}")

        # Initialize search service with user context
        search_service = SearchService(user_id=current_user.id)
        results = await search_service.search(query, threshold)
        logger.info(f"Found {len(results)} results")

        return JSONResponse(
            status_code=200,
            content={"results": results}
        )
    except Exception as e:
        logger.error(f"Error searching: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(
    question: str = Body(..., embed=True),
    current_user: UserResponse = Depends(get_local_user)
):
    """
    Conversational chat over memories using a real LLM (Poolside primary, OpenAI fallback).
    Searches memories for grounding context, then generates a grounded answer.
    Falls back to the top matching memory content if no LLM provider is available.
    """
    try:
        if not question or not question.strip():
            raise HTTPException(status_code=400, detail="Question is required")

        logger.info(f"Chat for user {current_user.id}: {question}")

        # Build an enriched search query: use the question plus extracted
        # keywords so semantic search retrieves relevant memories even when the
        # phrasing differs (e.g. "assignment submission dates" vs "assignment due").
        enriched_query = question
        lower_q = question.lower()
        # Pull out key nouns/phrases commonly relevant to LifeLog memories
        keywords = []
        for kw in ("assignment", "due", "deadline", "date", "submit", "submission",
                   "exam", "meeting", "event", "reminder", "task", "homework",
                   "page", "pages", "mathematics", "math", "professor"):
            if kw in lower_q:
                keywords.append(kw)
        if keywords:
            enriched_query = question + " " + " ".join(keywords)

        # Search memories for grounding context
        search_service = SearchService(user_id=current_user.id)
        results = await search_service.search(enriched_query, 0.3)

        context_parts = []
        for r in results[:5]:
            content = r.get("content") or ""
            tags = r.get("tags") or []
            summary = r.get("summary") or ""
            context_parts.append(f"- {content} (tags: {', '.join(tags)})")

        context = "\n\n".join(context_parts) if context_parts else "No memories found."

        # Generate an LLM-grounded answer
        answer = await poolside_service.generate_answer(question, context)

        # Fallback: if no LLM provider worked, return the top memory content
        if not answer:
            if results:
                top = results[0]
                answer = (
                    f"I couldn't generate an AI answer, but here's the most relevant memory I found:\n\n"
                    f"**{top.get('summary') or 'Relevant memory'}**\n\n{top.get('content')}"
                )
            else:
                answer = "I couldn't find any relevant information in your memories."

        return JSONResponse(
            status_code=200,
            content={
                "answer": answer,
                "sources": results[:5]
            }
        )
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memories")
async def get_memories(
    limit: int = 10,
    offset: int = 0,
    current_user: UserResponse = Depends(get_local_user)
):
    """
    Get list of memories for the current user
    """
    try:
        # Get from SQL database
        from database import get_memories_by_user
        
        memories = get_memories_by_user(current_user.id, limit, offset)
        
        # Convert to response format
        results = []
        for mem in memories:
            timestamp_str = mem.timestamp.isoformat() if hasattr(mem.timestamp, "isoformat") else str(mem.timestamp or "")
            results.append({
                "id": mem.id,
                "date": timestamp_str.split("T")[0] if timestamp_str else None,
                "time": timestamp_str.split("T")[1].split(".")[0] if timestamp_str and "T" in timestamp_str else None,
                "content": mem.content,
                "summary": mem.summary,
                "tags": mem.tags,
                "tasks": mem.tasks,
                "people": mem.people,
                "sentiment": mem.sentiment
            })
        
        return JSONResponse(
            status_code=200,
            content={"memories": results}
        )
    except Exception as e:
        logger.error(f"Error fetching memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memories/{memory_id}")
async def get_memory(
    memory_id: str,
    current_user: UserResponse = Depends(get_local_user)
):
    """
    Get a specific memory
    """
    try:
        from database import get_memory_by_id
        
        memory = get_memory_by_id(memory_id)
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        if memory.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this memory")
        
        timestamp_str = memory.timestamp.isoformat() if hasattr(memory.timestamp, "isoformat") else str(memory.timestamp or "")
        return JSONResponse(
            status_code=200,
            content={
                "id": memory.id,
                "date": timestamp_str.split("T")[0] if timestamp_str else None,
                "time": timestamp_str.split("T")[1].split(".")[0] if timestamp_str and "T" in timestamp_str else None,
                "content": memory.content,
                "summary": memory.summary,
                "sentiment": memory.sentiment,
                "tags": memory.tags,
                "topics": memory.topics,
                "tasks": memory.tasks,
                "people": memory.people,
                "dates": memory.dates,
                "action_items": memory.action_items,
                "filename": memory.filename,
                "source": memory.source
            }
        )
    except Exception as e:
        logger.error(f"Error fetching memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    current_user: UserResponse = Depends(get_local_user)
):
    """
    Delete a memory
    """
    try:
        from database import delete_memory, get_memory_by_id
        
        # Check if memory exists and belongs to user
        memory = get_memory_by_id(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        if memory.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this memory")
        
        # Delete from both databases
        success = delete_memory(memory_id, current_user.id)
        
        # Also delete from ChromaDB
        search_service = SearchService(user_id=current_user.id)
        await search_service.delete_memory(memory_id)
        
        return JSONResponse(
            status_code=200,
            content={"success": True}
        )
    except Exception as e:
        logger.error(f"Error deleting memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
