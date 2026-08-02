"""
Calendar MCP Server for LifeLog
Provides MCP tools for Google Calendar integration
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_server import BaseMCPServer, MCPServerConfig, MCPTool, create_input_schema

logger = logging.getLogger(__name__)


class CalendarMCPServer(BaseMCPServer):
    """MCP server for Google Calendar operations"""
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        
        # Define calendar tools
        calendar_tools = [
            MCPTool(
                name="list_calendars",
                description="List all Google calendars for the user",
                inputSchema=create_input_schema(
                    properties={},
                    required=[]
                ),
                handler=self.list_calendars
            ),
            MCPTool(
                name="list_events",
                description="List events from a calendar",
                inputSchema=create_input_schema(
                    properties={
                        "calendar_id": {"type": "string", "description": "Calendar ID (default: primary)", "default": "primary"},
                        "time_min": {"type": "string", "description": "Start time in ISO format", "default": None},
                        "time_max": {"type": "string", "description": "End time in ISO format", "default": None},
                        "max_results": {"type": "integer", "description": "Maximum number of events", "default": 50}
                    },
                    required=[]
                ),
                handler=self.list_events
            ),
            MCPTool(
                name="create_event",
                description="Create a new calendar event",
                inputSchema=create_input_schema(
                    properties={
                        "summary": {"type": "string", "description": "Event title"},
                        "start": {"type": "string", "description": "Start time in ISO format", "default": None},
                        "end": {"type": "string", "description": "End time in ISO format", "default": None},
                        "description": {"type": "string", "description": "Event description", "default": None},
                        "location": {"type": "string", "description": "Event location", "default": None},
                        "calendar_id": {"type": "string", "description": "Calendar ID (default: primary)", "default": "primary"}
                    },
                    required=["summary", "start", "end"]
                ),
                handler=self.create_event
            ),
            MCPTool(
                name="get_event",
                description="Get a specific calendar event",
                inputSchema=create_input_schema(
                    properties={
                        "calendar_id": {"type": "string", "description": "Calendar ID (default: primary)", "default": "primary"},
                        "event_id": {"type": "string", "description": "Event ID"}
                    },
                    required=["event_id"]
                ),
                handler=self.get_event
            ),
            MCPTool(
                name="delete_event",
                description="Delete a calendar event",
                inputSchema=create_input_schema(
                    properties={
                        "calendar_id": {"type": "string", "description": "Calendar ID (default: primary)", "default": "primary"},
                        "event_id": {"type": "string", "description": "Event ID"}
                    },
                    required=["event_id"]
                ),
                handler=self.delete_event
            ),
            MCPTool(
                name="get_freebusy",
                description="Get free/busy time slots for the user",
                inputSchema=create_input_schema(
                    properties={
                        "time_min": {"type": "string", "description": "Start time in ISO format", "default": None},
                        "time_max": {"type": "string", "description": "End time in ISO format", "default": None},
                        "calendar_ids": {"type": "array", "description": "List of calendar IDs to check", "items": {"type": "string"}, "default": ["primary"]}
                    },
                    required=[]
                ),
                handler=self.get_freebusy
            ),
            MCPTool(
                name="get_upcoming_events",
                description="Get upcoming events for the next N days",
                inputSchema=create_input_schema(
                    properties={
                        "days": {"type": "integer", "description": "Number of days to look ahead", "default": 7},
                        "max_results": {"type": "integer", "description": "Maximum number of events", "default": 20}
                    },
                    required=[]
                ),
                handler=self.get_upcoming_events
            ),
            MCPTool(
                name="get_todays_events",
                description="Get events for today",
                inputSchema=create_input_schema(
                    properties={},
                    required=[]
                ),
                handler=self.get_todays_events
            )
        ]
        
        config = MCPServerConfig(
            name="lifelog-calendar",
            version="1.0.0",
            capabilities={
                "tools": {},
                "resources": {}
            },
            tools=calendar_tools
        )
        
        super().__init__(config)
    
    async def _get_calendar_service(self):
        """Get authenticated calendar service for the user"""
        from services.google import get_calendar_service
        return get_calendar_service(self.user_id)
    
    async def list_calendars(self) -> List[Dict[str, Any]]:
        """List all Google calendars for the user"""
        try:
            service = await self._get_calendar_service()
            calendars = await service.list_calendars()
            
            return [
                {
                    "id": cal.get("id"),
                    "summary": cal.get("summary"),
                    "description": cal.get("description"),
                    "primary": cal.get("primary", False),
                    "timeZone": cal.get("timeZone")
                }
                for cal in calendars
            ]
        except Exception as e:
            logger.error(f"Error listing calendars: {str(e)}")
            return []
    
    async def list_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """List events from a calendar"""
        try:
            service = await self._get_calendar_service()
            
            # Set default time range if not provided
            if not time_min:
                time_min = datetime.utcnow().isoformat() + "Z"
            if not time_max:
                time_max = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
            
            events = await service.list_events(calendar_id, time_min, time_max)
            
            return [
                {
                    "id": event.get("id"),
                    "summary": event.get("summary"),
                    "description": event.get("description"),
                    "start": event.get("start"),
                    "end": event.get("end"),
                    "location": event.get("location"),
                    "htmlLink": event.get("htmlLink"),
                    "created": event.get("created"),
                    "updated": event.get("updated"),
                    "status": event.get("status"),
                    "organizer": event.get("organizer"),
                    "attendees": event.get("attendees", []),
                    "calendar_id": calendar_id
                }
                for event in events
            ]
        except Exception as e:
            logger.error(f"Error listing events: {str(e)}")
            return []
    
    async def create_event(
        self,
        summary: str,
        start: str,
        end: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        calendar_id: str = "primary"
    ) -> Dict[str, Any]:
        """Create a new calendar event"""
        try:
            service = await self._get_calendar_service()
            event = await service.create_event(
                summary=summary,
                start=start,
                end=end,
                description=description,
                location=location,
                calendar_id=calendar_id
            )
            
            return {
                "success": True,
                "event": {
                    "id": event.get("id"),
                    "summary": event.get("summary"),
                    "start": event.get("start"),
                    "end": event.get("end"),
                    "htmlLink": event.get("htmlLink"),
                    "calendar_id": calendar_id
                },
                "message": "Event created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating event: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_event(self, event_id: str, calendar_id: str = "primary") -> Dict[str, Any]:
        """Get a specific calendar event"""
        try:
            service = await self._get_calendar_service()
            event = await service.get_event(calendar_id, event_id)
            
            return {
                "success": True,
                "event": {
                    "id": event.get("id"),
                    "summary": event.get("summary"),
                    "description": event.get("description"),
                    "start": event.get("start"),
                    "end": event.get("end"),
                    "location": event.get("location"),
                    "htmlLink": event.get("htmlLink"),
                    "created": event.get("created"),
                    "updated": event.get("updated"),
                    "status": event.get("status"),
                    "organizer": event.get("organizer"),
                    "attendees": event.get("attendees", [])
                }
            }
        except Exception as e:
            logger.error(f"Error getting event: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def delete_event(self, event_id: str, calendar_id: str = "primary") -> Dict[str, Any]:
        """Delete a calendar event"""
        try:
            service = await self._get_calendar_service()
            success = await service.delete_event(calendar_id, event_id)
            
            return {
                "success": success,
                "message": "Event deleted successfully" if success else "Event not found"
            }
        except Exception as e:
            logger.error(f"Error deleting event: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_freebusy(
        self,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        calendar_ids: List[str] = None
    ) -> Dict[str, Any]:
        """Get free/busy time slots for the user"""
        try:
            service = await self._get_calendar_service()
            
            if not calendar_ids:
                calendar_ids = ["primary"]
            
            # For simplicity, we'll just get freebusy for the primary calendar
            # In a full implementation, we'd aggregate across multiple calendars
            result = await service.freebusy(time_min, time_max)
            
            return {
                "success": True,
                "freebusy": result,
                "calendars": calendar_ids
            }
        except Exception as e:
            logger.error(f"Error getting free/busy: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_upcoming_events(self, days: int = 7, max_results: int = 20) -> List[Dict[str, Any]]:
        """Get upcoming events for the next N days"""
        try:
            time_min = datetime.utcnow().isoformat() + "Z"
            time_max = (datetime.utcnow() + timedelta(days=days)).isoformat() + "Z"
            
            events = await self.list_events("primary", time_min, time_max, max_results)
            
            # Sort by start time
            events.sort(key=lambda x: x.get("start", {}).get("dateTime", ""))
            
            return events
        except Exception as e:
            logger.error(f"Error getting upcoming events: {str(e)}")
            return []
    
    async def get_todays_events(self) -> List[Dict[str, Any]]:
        """Get events for today"""
        try:
            today = datetime.utcnow()
            time_min = today.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
            time_max = today.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + "Z"
            
            events = await self.list_events("primary", time_min, time_max, 50)
            
            # Sort by start time
            events.sort(key=lambda x: x.get("start", {}).get("dateTime", ""))
            
            return events
        except Exception as e:
            logger.error(f"Error getting today's events: {str(e)}")
            return []


# Singleton instance
calendar_mcp_server = CalendarMCPServer()