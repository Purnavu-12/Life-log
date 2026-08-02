"""
Google OAuth and API service for Calendar and Gmail integration
"""

import os
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
from fastapi import HTTPException, status
import requests

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import httpx
import secrets
import hashlib
import base64

from models.google import GoogleCredentials, GoogleTokenResponse, GoogleUserInfo
from database import get_google_credentials, save_google_credentials, delete_google_credentials

logger = logging.getLogger(__name__)

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Calendar scopes
CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]

# Gmail scopes (read-only for indexing)
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
]

# Full scopes for both
FULL_SCOPES = CALENDAR_SCOPES + GMAIL_SCOPES


class GoogleOAuthService:
    """Service for handling Google OAuth flows"""
    
    def __init__(self):
        self.client_id = GOOGLE_CLIENT_ID
        self.client_secret = GOOGLE_CLIENT_SECRET
        self.redirect_uri = GOOGLE_REDIRECT_URI
        
        # Initialize OAuth flow
        self.flow = self._create_flow()
        
        # Store code verifiers for PKCE (in production, use Redis or database)
        # Format: {state: code_verifier}
        self.code_verifiers = {}

    def _generate_pkce_pair(self) -> tuple:
        """Generate PKCE code verifier and code challenge"""
        # Generate a random code verifier
        code_verifier = secrets.token_urlsafe(96)
        
        # Create code challenge by SHA-256 hashing the verifier
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip("=")
        
        return code_verifier, code_challenge
    
    def _create_flow(self, scopes: List[str] = None):
        """Create OAuth flow with specified scopes"""
        if scopes is None:
            scopes = FULL_SCOPES
        
        if not self.client_id or not self.client_secret:
            logger.warning("Google OAuth credentials not configured")
            return None
        
        # Create client configuration from environment variables
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uris": [self.redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
        
        return Flow.from_client_config(
            client_config=client_config,
            scopes=scopes,
            redirect_uri=self.redirect_uri
        )
    
    def get_authorization_url(self, state: str = None, scopes: List[str] = None) -> str:
        """Generate Google OAuth authorization URL with PKCE"""
        if not self.flow:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth not configured"
            )
        
        # Generate PKCE pair
        code_verifier, code_challenge = self._generate_pkce_pair()
        
        # Store code verifier with state (or generate state if not provided)
        if not state:
            state = secrets.token_urlsafe(32)
        self.code_verifiers[state] = code_verifier
        
        if scopes:
            flow = self._create_flow(scopes)
        else:
            flow = self.flow
        
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
            code_challenge=code_challenge,
            code_challenge_method="S256"
        )
        return authorization_url
    
    async def exchange_code_for_token(self, code: str, state: str = None) -> GoogleCredentials:
        """Exchange authorization code for access token with PKCE"""
        if not self.flow:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth not configured"
            )
        
        try:
            # Get the code verifier from storage
            code_verifier = self.code_verifiers.get(state)
            if not code_verifier and state:
                # Try to find by state
                code_verifier = self.code_verifiers.pop(state, None)
            
            # Manually exchange code (Flow.fetch_token is synchronous)
            token_data = self._exchange_code(code, code_verifier)
            
            # Get user info
            user_info = await self._get_user_info(token_data["access_token"])
            
            # Create credentials object
            expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            
            return GoogleCredentials(
                user_id="",  # Will be set when saving
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_type=token_data["token_type"],
                expires_at=expires_at,
                scopes=token_data["scope"].split() if "scope" in token_data else FULL_SCOPES,
                google_user_id=user_info.id,
                email=user_info.email
            )
        except Exception as e:
            logger.error(f"Error exchanging code: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange code: {str(e)}"
            )
    
    def _exchange_code(self, code: str, code_verifier: str = None) -> Dict[str, Any]:
        """Exchange code for token using HTTP request with PKCE"""
        
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code"
        }
        
        # Add PKCE code verifier if available
        if code_verifier:
            data["code_verifier"] = code_verifier
        
        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data=data,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Token exchange failed: {response.text}")
        
        return response.json()
    
    async def _get_user_info(self, access_token: str) -> GoogleUserInfo:
        """Get Google user info from access token"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get user info: {response.text}")
            
            return GoogleUserInfo(**response.json())
    
    def save_credentials(self, credentials: GoogleCredentials, user_id: str) -> GoogleCredentials:
        """Save credentials for a user"""
        credentials.user_id = user_id
        return save_google_credentials(credentials)
    
    def get_credentials(self, user_id: str) -> Optional[GoogleCredentials]:
        """Get saved credentials for a user"""
        return get_google_credentials(user_id)
    
    def delete_credentials(self, user_id: str) -> bool:
        """Delete saved credentials for a user"""
        return delete_google_credentials(user_id)
    
    def get_credentials_for_api(self, user_id: str) -> Optional[Credentials]:
        """Get Google API credentials object for a user"""
        creds = self.get_credentials(user_id)
        if not creds:
            return None
        
        return Credentials(
            token=creds.access_token,
            refresh_token=creds.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=creds.scopes
        )


class GoogleCalendarService:
    """Service for Google Calendar API operations"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.oauth_service = GoogleOAuthService()
    
    def _get_client(self):
        """Get authenticated Calendar API client"""
        credentials = self.oauth_service.get_credentials_for_api(self.user_id)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google Calendar not connected. Please connect in settings."
            )
        
        # Check if token is expired and refresh if needed
        if credentials.expired and credentials.refresh_token:
            try:
                # Use synchronous requests for token refresh as expected by google-auth
                credentials.refresh(requests.Request())
                # Save refreshed credentials
                expires_at = credentials.expiry
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at)
                self.oauth_service.save_credentials(
                    GoogleCredentials(
                        user_id=self.user_id,
                        access_token=credentials.token,
                        refresh_token=credentials.refresh_token,
                        token_type=credentials.token_type,
                        expires_at=expires_at,
                        scopes=list(credentials.scopes),
                        google_user_id=None,
                        email=None
                    ),
                    self.user_id
                )
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Google token expired. Please re-connect."
                )
        
        return build('calendar', 'v3', credentials=credentials)
    
    async def freebusy(self, time_min: str = None, time_max: str = None) -> Dict[str, Any]:
        """Query free/busy status across calendars"""
        try:
            client = self._get_client()
            if not time_min:
                time_min = datetime.utcnow().isoformat() + "Z"
            if not time_max:
                time_max = (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"
            response = await asyncio.to_thread(
                client.freebusy().query,
                body={
                    "timeMin": time_min,
                    "timeMax": time_max,
                    "timeZone": "UTC",
                    "items": [{"id": "primary"}]
                }
            )
            response = await asyncio.to_thread(response.execute)
            return response
        except HttpError as e:
            logger.error(f"Freebusy error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to fetch free/busy: {str(e)}"
            )
    
    async def list_calendars(self) -> List[Dict[str, Any]]:
        """List all calendars for the user"""
        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.calendarList().list().execute
            )
            return response.get('items', [])
        except HttpError as e:
            logger.error(f"Calendar list error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to list calendars: {str(e)}"
            )
    
    async def list_events(self, calendar_id: str = "primary", time_min: str = None, time_max: str = None) -> List[Dict[str, Any]]:
        """List events from a calendar"""
        try:
            client = self._get_client()
            
            # Set default time range (next 30 days)
            if not time_min:
                time_min = datetime.utcnow().isoformat() + "Z"
            if not time_max:
                time_max = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
            
            response = await asyncio.to_thread(
                client.events().list,
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            )
            response = await asyncio.to_thread(response.execute)
            return response.get('items', [])
        except HttpError as e:
            logger.error(f"Events list error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to list events: {str(e)}"
            )
    
    async def get_event(self, calendar_id: str, event_id: str) -> Dict[str, Any]:
        """Get a specific event"""
        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.events().get,
                calendarId=calendar_id,
                eventId=event_id
            )
            response = await asyncio.to_thread(response.execute)
            return response
        except HttpError as e:
            logger.error(f"Get event error: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
    
    async def create_event(
        self,
        summary: str,
        start: str,
        end: str,
        description: str = None,
        location: str = None,
        calendar_id: str = "primary"
    ) -> Dict[str, Any]:
        """Create a new calendar event"""
        try:
            client = self._get_client()
            
            event = {
                'summary': summary,
                'start': {'dateTime': start},
                'end': {'dateTime': end},
            }
            
            if description:
                event['description'] = description
            if location:
                event['location'] = location
            
            response = await asyncio.to_thread(
                client.events().insert,
                calendarId=calendar_id,
                body=event
            )
            response = await asyncio.to_thread(response.execute)
            return response
        except HttpError as e:
            logger.error(f"Create event error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create event: {str(e)}"
            )
    
    async def delete_event(self, calendar_id: str, event_id: str) -> bool:
        """Delete an event"""
        try:
            client = self._get_client()
            await asyncio.to_thread(
                client.events().delete,
                calendarId=calendar_id,
                eventId=event_id
            )
            return True
        except HttpError as e:
            logger.error(f"Delete event error: {e}")
            return False


class GoogleGmailService:
    """Service for Google Gmail API operations"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.oauth_service = GoogleOAuthService()
    
    def _get_client(self):
        """Get authenticated Gmail API client"""
        credentials = self.oauth_service.get_credentials_for_api(self.user_id)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Gmail not connected. Please connect in settings."
            )
        
        # Check if token is expired and refresh if needed
        if credentials.expired and credentials.refresh_token:
            try:
                # Use synchronous requests for token refresh as expected by google-auth
                credentials.refresh(requests.Request())
                # Save refreshed credentials
                expires_at = credentials.expiry
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at)
                self.oauth_service.save_credentials(
                    GoogleCredentials(
                        user_id=self.user_id,
                        access_token=credentials.token,
                        refresh_token=credentials.refresh_token,
                        token_type=credentials.token_type,
                        expires_at=expires_at,
                        scopes=list(credentials.scopes),
                        google_user_id=None,
                        email=None
                    ),
                    self.user_id
                )
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Gmail token expired. Please re-connect."
                )
        
        return build('gmail', 'v1', credentials=credentials)
    
    async def list_important(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """List important unread messages from Gmail"""
        return await self.list_messages(query="is:important is:unread", max_results=max_results)
    
    async def list_messages(self, query: str = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """List messages from Gmail"""
        try:
            client = self._get_client()
            
            request = client.users().messages().list(
                userId='me',
                maxResults=max_results
            )
            
            if query:
                request = client.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=max_results
                )
            
            response = await asyncio.to_thread(request.execute)
            messages = response.get('messages', [])
            
            # Get full message details
            full_messages = []
            for msg in messages:
                full_msg = await self.get_message(msg['id'])
                full_messages.append(full_msg)
            
            return full_messages
        except HttpError as e:
            logger.error(f"List messages error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to list messages: {str(e)}"
            )
    
    async def get_message(self, message_id: str) -> Dict[str, Any]:
        """Get a specific message"""
        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.users().messages().get,
                userId='me',
                id=message_id,
                format='full'
            )
            response = await asyncio.to_thread(response.execute)
            return response
        except HttpError as e:
            logger.error(f"Get message error: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
    
    async def get_profile(self) -> Dict[str, Any]:
        """Get Gmail profile"""
        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.users().getProfile,
                userId='me'
            )
            response = await asyncio.to_thread(response.execute)
            return response
        except HttpError as e:
            logger.error(f"Get profile error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get profile: {str(e)}"
            )
    
    async def index_emails(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Index recent emails for search"""
        messages = await self.list_messages(max_results=limit)
        indexed = []
        
        for msg in messages:
            # Extract relevant information
            headers = msg.get('payload', {}).get('headers', [])
            header_dict = {h['name'].lower(): h['value'] for h in headers}
            
            body = self._extract_body(msg)
            
            indexed.append({
                'id': msg['id'],
                'thread_id': msg.get('threadId'),
                'subject': header_dict.get('subject', ''),
                'from': header_dict.get('from', ''),
                'to': header_dict.get('to', ''),
                'date': header_dict.get('date', ''),
                'body': body,
                'snippet': msg.get('snippet', ''),
                'labels': msg.get('labelIds', []),
                'raw': msg
            })
        
        return indexed
    
    def _extract_body(self, message: Dict[str, Any]) -> str:
        """Extract plain text body from message"""
        payload = message.get('payload', {})
        parts = payload.get('parts', [])
        
        # Look for text/plain or text/html
        for part in parts:
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    import base64
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        # Try body directly
        body = payload.get('body', {})
        if body:
            import base64
            data = body.get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return message.get('snippet', '')


# Singleton instances
google_oauth_service = GoogleOAuthService()


# Helper function to get calendar service for a user
def get_calendar_service(user_id: str) -> GoogleCalendarService:
    """Get calendar service for a user"""
    return GoogleCalendarService(user_id)


# Helper function to get gmail service for a user
def get_gmail_service(user_id: str) -> GoogleGmailService:
    """Get gmail service for a user"""
    return GoogleGmailService(user_id)
