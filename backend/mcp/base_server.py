"""
Base MCP server implementation
Provides common functionality for LifeLog MCP servers
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class MCPMessageType(str, Enum):
    """MCP message types"""
    NOTIFICATION = "notification"
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"


@dataclass
class MCPTool:
    """Represents an MCP tool"""
    name: str
    description: str
    inputSchema: Dict[str, Any]
    handler: Callable[..., Awaitable[Any]]


@dataclass
class MCPServerConfig:
    """Configuration for MCP server"""
    name: str
    version: str = "1.0.0"
    capabilities: Dict[str, Any] = field(default_factory=dict)
    tools: List[MCPTool] = field(default_factory=list)


class BaseMCPServer:
    """Base class for MCP servers"""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.tools: Dict[str, MCPTool] = {tool.name: tool for tool in config.tools}
        self.running = False
        self.server_task: Optional[asyncio.Task] = None
        
    async def start(self, host: str = "0.0.0.0", port: int = 8080):
        """Start the MCP server"""
        self.running = True
        logger.info(f"Starting {self.config.name} MCP server on {host}:{port}")
        
        # In a real implementation, this would start a server that communicates
        # via MCP protocol (usually stdio or HTTP)
        # For now, we'll implement as a simple tool registry
        
    async def stop(self):
        """Stop the MCP server"""
        self.running = False
        if self.server_task:
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass
        logger.info(f"Stopped {self.config.name} MCP server")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a registered tool"""
        if tool_name not in self.tools:
            return {
                "error": f"Tool '{tool_name}' not found",
                "success": False
            }
        
        tool = self.tools[tool_name]
        
        try:
            # Validate arguments against schema
            validated_args = self._validate_arguments(arguments, tool.inputSchema)
            
            # Call the tool handler
            result = await tool.handler(**validated_args)
            
            return {
                "success": True,
                "result": result,
                "tool": tool_name
            }
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {str(e)}")
            return {
                "error": str(e),
                "success": False,
                "tool": tool_name
            }
    
    def _validate_arguments(self, arguments: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tool arguments against schema"""
        # Simple validation - in a real implementation, use JSON Schema validation
        validated = {}
        
        if "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                if prop_name in arguments:
                    validated[prop_name] = arguments[prop_name]
                elif prop_schema.get("required", False):
                    raise ValueError(f"Missing required argument: {prop_name}")
        
        return validated
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            }
            for tool in self.tools.values()
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            "status": "healthy" if self.running else "stopped",
            "server": self.config.name,
            "version": self.config.version,
            "tool_count": len(self.tools)
        }


def create_input_schema(
    properties: Dict[str, Any],
    required: List[str] = None
) -> Dict[str, Any]:
    """Create JSON Schema for tool input"""
    return {
        "type": "object",
        "properties": properties,
        "required": required or []
    }