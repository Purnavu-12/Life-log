"""
Memory MCP Server for LifeLog
Provides MCP tools for memory management
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_server import BaseMCPServer, MCPServerConfig, MCPTool, create_input_schema
from database import get_memories_by_user, create_memory, delete_memory, get_memory_by_id
from models.memory import MemoryCreate

logger = logging.getLogger(__name__)


class MemoryMCPServer(BaseMCPServer):
    """MCP server for memory operations"""
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        
        # Define memory tools
        memory_tools = [
            MCPTool(
                name="search_memories",
                description="Search user memories using semantic search",
                inputSchema=create_input_schema(
                    properties={
                        "query": {"type": "string", "description": "Search query"},
                        "threshold": {"type": "number", "description": "Similarity threshold (0-1)", "default": 0.5},
                        "limit": {"type": "integer", "description": "Maximum number of results", "default": 10}
                    },
                    required=["query"]
                ),
                handler=self.search_memories
            ),
            MCPTool(
                name="list_memories",
                description="List memories for the current user",
                inputSchema=create_input_schema(
                    properties={
                        "limit": {"type": "integer", "description": "Maximum number of memories", "default": 10},
                        "offset": {"type": "integer", "description": "Offset for pagination", "default": 0},
                        "tags": {"type": "array", "description": "Filter by tags", "items": {"type": "string"}}
                    },
                    required=[]
                ),
                handler=self.list_memories
            ),
            MCPTool(
                name="create_memory",
                description="Create a new memory",
                inputSchema=create_input_schema(
                    properties={
                        "content": {"type": "string", "description": "Memory content"},
                        "summary": {"type": "string", "description": "Memory summary"},
                        "tags": {"type": "array", "description": "Tags for the memory", "items": {"type": "string"}},
                        "sentiment": {"type": "string", "description": "Sentiment analysis result"},
                        "people": {"type": "array", "description": "People mentioned", "items": {"type": "string"}},
                        "tasks": {"type": "array", "description": "Tasks mentioned", "items": {"type": "string"}},
                        "topics": {"type": "array", "description": "Topics discussed", "items": {"type": "string"}},
                        "dates": {"type": "array", "description": "Dates mentioned", "items": {"type": "string"}},
                        "filename": {"type": "string", "description": "Original filename"},
                        "source": {"type": "string", "description": "Source of memory", "default": "mcp"}
                    },
                    required=["content"]
                ),
                handler=self.create_memory_tool
            ),
            MCPTool(
                name="get_memory",
                description="Get a specific memory by ID",
                inputSchema=create_input_schema(
                    properties={
                        "memory_id": {"type": "string", "description": "Memory ID"}
                    },
                    required=["memory_id"]
                ),
                handler=self.get_memory_tool
            ),
            MCPTool(
                name="delete_memory",
                description="Delete a memory",
                inputSchema=create_input_schema(
                    properties={
                        "memory_id": {"type": "string", "description": "Memory ID"}
                    },
                    required=["memory_id"]
                ),
                handler=self.delete_memory_tool
            ),
            MCPTool(
                name="get_memory_stats",
                description="Get memory statistics for the user",
                inputSchema=create_input_schema(
                    properties={},
                    required=[]
                ),
                handler=self.get_memory_stats
            )
        ]
        
        config = MCPServerConfig(
            name="lifelog-memory",
            version="1.0.0",
            capabilities={
                "tools": {},
                "resources": {}
            },
            tools=memory_tools
        )
        
        super().__init__(config)
    
    async def search_memories(self, query: str, threshold: float = 0.5, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories using semantic search"""
        try:
            from services.search import SearchService
            
            search_service = SearchService(user_id=self.user_id)
            results = await search_service.search(query, threshold, limit)
            
            return [
                {
                    "id": result.get("id"),
                    "date": result.get("date"),
                    "content": result.get("content"),
                    "similarity": result.get("similarity"),
                    "tags": result.get("tags", []),
                    "summary": result.get("summary")
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return []
    
    async def list_memories(self, limit: int = 10, offset: int = 0, tags: List[str] = None) -> List[Dict[str, Any]]:
        """List memories for the user"""
        try:
            memories = get_memories_by_user(self.user_id, limit, offset)
            
            # Filter by tags if specified
            if tags:
                memories = [
                    mem for mem in memories 
                    if any(tag in (mem.tags or []) for tag in tags)
                ]
            
            return [
                {
                    "id": mem.id,
                    "date": mem.timestamp.isoformat() if hasattr(mem.timestamp, "isoformat") else str(mem.timestamp),
                    "content": mem.content,
                    "summary": mem.summary,
                    "tags": mem.tags or [],
                    "sentiment": mem.sentiment,
                    "filename": mem.filename,
                    "source": mem.source,
                    "people": mem.people or [],
                    "tasks": mem.tasks or []
                }
                for mem in memories
            ]
        except Exception as e:
            logger.error(f"Error listing memories: {str(e)}")
            return []
    
    async def create_memory_tool(
        self, 
        content: str,
        summary: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sentiment: Optional[str] = None,
        people: Optional[List[str]] = None,
        tasks: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        dates: Optional[List[str]] = None,
        filename: Optional[str] = None,
        source: str = "mcp"
    ) -> Dict[str, Any]:
        """Create a new memory"""
        try:
            memory_data = MemoryCreate(
                content=content,
                summary=summary,
                sentiment=sentiment,
                tags=tags or [],
                topics=topics or [],
                tasks=tasks or [],
                people=people or [],
                dates=dates or [],
                filename=filename,
                source=source
            )
            
            db_memory = create_memory(memory_data, self.user_id)
            
            return {
                "success": True,
                "memory_id": db_memory.id,
                "message": "Memory created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating memory: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_memory_tool(self, memory_id: str) -> Dict[str, Any]:
        """Get a specific memory"""
        try:
            memory = get_memory_by_id(memory_id)
            if not memory:
                return {"success": False, "error": "Memory not found"}
            
            timestamp_str = memory.timestamp.isoformat() if hasattr(memory.timestamp, "isoformat") else str(memory.timestamp or "")
            
            return {
                "success": True,
                "memory": {
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
            }
        except Exception as e:
            logger.error(f"Error getting memory: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def delete_memory_tool(self, memory_id: str) -> Dict[str, Any]:
        """Delete a memory"""
        try:
            success = delete_memory(memory_id, self.user_id)
            return {
                "success": success,
                "message": "Memory deleted successfully" if success else "Memory not found or not authorized"
            }
        except Exception as e:
            logger.error(f"Error deleting memory: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        try:
            memories = get_memories_by_user(self.user_id, 1000, 0)
            
            total_memories = len(memories)
            
            # Count by source
            sources: Dict[str, int] = {}
            for mem in memories:
                source = mem.source or "unknown"
                sources[source] = sources.get(source, 0) + 1
            
            # Count by sentiment
            sentiments: Dict[str, int] = {}
            for mem in memories:
                sentiment = mem.sentiment or "neutral"
                sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
            
            # Count tags
            all_tags = []
            for mem in memories:
                all_tags.extend(mem.tags or [])
            
            return {
                "success": True,
                "total_memories": total_memories,
                "sources": sources,
                "sentiments": sentiments,
                "unique_tags": len(set(all_tags)),
                "total_tags": len(all_tags)
            }
        except Exception as e:
            logger.error(f"Error getting memory stats: {str(e)}")
            return {"success": False, "error": str(e)}


# Singleton instance
memory_mcp_server = MemoryMCPServer()