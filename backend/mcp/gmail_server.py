"""
Gmail MCP Server for LifeLog
Provides MCP tools for Gmail integration
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_server import BaseMCPServer, MCPServerConfig, MCPTool, create_input_schema

logger = logging.getLogger(__name__)


class GmailMCPServer(BaseMCPServer):
    """MCP server for Gmail operations"""
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        
        # Define gmail tools
        gmail_tools = [
            MCPTool(
                name="list_messages",
                description="List messages from Gmail with optional query",
                inputSchema=create_input_schema(
                    properties={
                        "query": {"type": "string", "description": "Gmail search query", "default": None},
                        "max_results": {"type": "integer", "description": "Maximum number of messages", "default": 10},
                        "include_body": {"type": "boolean", "description": "Include message body in results", "default": False}
                    },
                    required=[]
                ),
                handler=self.list_messages
            ),
            MCPTool(
                name="get_message",
                description="Get a specific email message",
                inputSchema=create_input_schema(
                    properties={
                        "message_id": {"type": "string", "description": "Message ID"},
                        "include_body": {"type": "boolean", "description": "Include full message body", "default": True}
                    },
                    required=["message_id"]
                ),
                handler=self.get_message
            ),
            MCPTool(
                name="list_important_messages",
                description="List important unread messages",
                inputSchema=create_input_schema(
                    properties={
                        "max_results": {"type": "integer", "description": "Maximum number of messages", "default": 10}
                    },
                    required=[]
                ),
                handler=self.list_important_messages
            ),
            MCPTool(
                name="list_unread_messages",
                description="List unread messages",
                inputSchema=create_input_schema(
                    properties={
                        "max_results": {"type": "integer", "description": "Maximum number of messages", "default": 10}
                    },
                    required=[]
                ),
                handler=self.list_unread_messages
            ),
            MCPTool(
                name="search_messages",
                description="Search messages with a query",
                inputSchema=create_input_schema(
                    properties={
                        "query": {"type": "string", "description": "Gmail search query"},
                        "max_results": {"type": "integer", "description": "Maximum number of results", "default": 10}
                    },
                    required=["query"]
                ),
                handler=self.search_messages
            ),
            MCPTool(
                name="get_profile",
                description="Get Gmail user profile",
                inputSchema=create_input_schema(
                    properties={},
                    required=[]
                ),
                handler=self.get_profile
            ),
            MCPTool(
                name="get_recent_messages",
                description="Get recent messages from the inbox",
                inputSchema=create_input_schema(
                    properties={
                        "max_results": {"type": "integer", "description": "Maximum number of messages", "default": 10},
                        "days": {"type": "integer", "description": "Number of days to look back", "default": 7}
                    },
                    required=[]
                ),
                handler=self.get_recent_messages
            ),
            MCPTool(
                name="get_message_count",
                description="Get count of messages by category",
                inputSchema=create_input_schema(
                    properties={},
                    required=[]
                ),
                handler=self.get_message_count
            )
        ]
        
        config = MCPServerConfig(
            name="lifelog-gmail",
            version="1.0.0",
            capabilities={
                "tools": {},
                "resources": {}
            },
            tools=gmail_tools
        )
        
        super().__init__(config)
    
    async def _get_gmail_service(self):
        """Get authenticated gmail service for the user"""
        from services.google import get_gmail_service
        return get_gmail_service(self.user_id)
    
    async def list_messages(
        self,
        query: Optional[str] = None,
        max_results: int = 10,
        include_body: bool = False
    ) -> List[Dict[str, Any]]:
        """List messages from Gmail"""
        try:
            service = await self._get_gmail_service()
            messages = await service.list_messages(query, max_results)
            
            return [
                self._format_message(msg, include_body)
                for msg in messages
            ]
        except Exception as e:
            logger.error(f"Error listing messages: {str(e)}")
            return []
    
    async def get_message(self, message_id: str, include_body: bool = True) -> Dict[str, Any]:
        """Get a specific email message"""
        try:
            service = await self._get_gmail_service()
            message = await service.get_message(message_id)
            
            return {
                "success": True,
                "message": self._format_message(message, include_body)
            }
        except Exception as e:
            logger.error(f"Error getting message: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def list_important_messages(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """List important unread messages"""
        try:
            service = await self._get_gmail_service()
            messages = await service.list_important(max_results)
            
            return [
                self._format_message(msg, True)
                for msg in messages
            ]
        except Exception as e:
            logger.error(f"Error listing important messages: {str(e)}")
            return []
    
    async def list_unread_messages(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """List unread messages"""
        try:
            service = await self._get_gmail_service()
            messages = await service.list_messages("is:unread", max_results)
            
            return [
                self._format_message(msg, True)
                for msg in messages
            ]
        except Exception as e:
            logger.error(f"Error listing unread messages: {str(e)}")
            return []
    
    async def search_messages(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search messages with a query"""
        return await self.list_messages(query, max_results, True)
    
    async def get_profile(self) -> Dict[str, Any]:
        """Get Gmail user profile"""
        try:
            service = await self._get_gmail_service()
            profile = await service.get_profile()
            
            return {
                "success": True,
                "profile": {
                    "email": profile.get("emailAddress"),
                    "messages_total": profile.get("messagesTotal"),
                    "threads_total": profile.get("threadsTotal")
                }
            }
        except Exception as e:
            logger.error(f"Error getting profile: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_recent_messages(self, max_results: int = 10, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent messages from the inbox"""
        try:
            # Calculate date range
            start_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
            query = f"after:{start_date}"
            
            return await self.list_messages(query, max_results, True)
        except Exception as e:
            logger.error(f"Error getting recent messages: {str(e)}")
            return []
    
    async def get_message_count(self) -> Dict[str, Any]:
        """Get count of messages by category"""
        try:
            service = await self._get_gmail_service()
            profile = await service.get_profile()
            
            # Get counts for different categories
            categories = {
                "important_unread": 0,
                "unread": 0,
                "total": profile.get("messagesTotal", 0)
            }
            
            try:
                important = await service.list_important(1)  # Just to check count
                categories["important_unread"] = len(important)
            except:
                pass
            
            try:
                unread = await service.list_messages("is:unread", 1)
                categories["unread"] = len(unread)
            except:
                pass
            
            return {
                "success": True,
                "counts": categories
            }
        except Exception as e:
            logger.error(f"Error getting message count: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _format_message(self, message: Dict[str, Any], include_body: bool = False) -> Dict[str, Any]:
        """Format a message for consistent output"""
        headers = message.get('payload', {}).get('headers', [])
        header_dict = {h.get('name', '').lower(): h.get('value', '') for h in headers}
        
        formatted = {
            "id": message.get("id"),
            "thread_id": message.get("threadId"),
            "subject": header_dict.get('subject', '(No Subject)'),
            "from": header_dict.get('from', 'Unknown'),
            "to": header_dict.get('to', ''),
            "date": header_dict.get('date', ''),
            "snippet": message.get("snippet", ''),
            "label_ids": message.get("labelIds", []),
            "size": message.get("sizeEstimate", 0)
        }
        
        if include_body:
            formatted["body"] = self._extract_body(message)
        
        return formatted
    
    def _extract_body(self, message: Dict[str, Any]) -> str:
        """Extract plain text body from message"""
        try:
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
        except Exception:
            return message.get('snippet', '')


# Singleton instance
gmail_mcp_server = GmailMCPServer()