#!/usr/bin/env python3
"""
MCP Builder Server - Builds MCP servers based on platform APIs
Standard MCP Server Implementation
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Optional, Dict, List
from pathlib import Path
import os
import sys

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.requests import Request
import uvicorn

# User management
user_db = {}  # email -> uuid mapping

# Platform viability cache
platform_cache = {}

def get_user_uuid(email: str = None) -> str:
    """Get fixed UUID for public access"""
    # Return fixed UUID with all 1s for public access
    return "11111111-1111-1111-1111-111111111111"

def get_builds_path(user_uuid: str, platform: str, version: int) -> Path:
    """Get the path for builds storage"""
    base_path = Path(__file__).parent / "builds"
    return base_path / user_uuid / platform / str(version)

async def assess_platform_api(platform: str) -> Dict[str, Any]:
    """Assess if platform API is viable for MCP server creation"""
    # Simulate API assessment logic
    # In real implementation, this would analyze the platform's API
    
    known_platforms = {
        "github": {"viable": True, "oauth_required": False},
        "gmail": {"viable": True, "oauth_required": False}, 
        "slack": {"viable": True, "oauth_required": False},
        "twitter": {"viable": True, "oauth_required": False},
        "discord": {"viable": True, "oauth_required": False},
        "notion": {"viable": True, "oauth_required": False},
    }
    
    if platform.lower() in known_platforms:
        return known_platforms[platform.lower()]
    
    # For unknown platforms, return as potentially viable but needs assessment
    return {"viable": True, "oauth_required": False, "needs_research": True}

def get_available_tools():
    """List available tools"""
    return [
        {
            "name": "is_building_mcp_server_viable",
            "description": "Check if building an MCP server for a platform is viable",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "description": "Name of the platform to assess"
                    }
                },
                "required": ["platform"]
            }
        },
        {
            "name": "build_mcp_server", 
            "description": "Build an MCP server for the specified platform",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "description": "Name of the platform"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of what the MCP server should do"
                    }
                },
                "required": ["platform", "description"]
            }
        }
    ]

async def handle_tool_call(name: str, arguments: dict):
    """Handle tool calls"""
    if name == "is_building_mcp_server_viable":
        platform = arguments.get("platform")
        if not platform:
            return {"error": "platform is required"}
        
        # Assess platform viability
        assessment = await assess_platform_api(platform)
        
        if assessment["viable"]:
            required_params = {
                "platform_name": platform,
                "description": "Required - Description of what the MCP server should do"
            }
            
            response = {
                "viable": True,
                "message": f"Building an MCP server for {platform} is viable",
                "required_parameters": required_params
            }
        else:
            response = {
                "viable": False,
                "message": f"Building an MCP server for {platform} is not currently supported"
            }
            
        return {"text": json.dumps(response, indent=2)}
    
    elif name == "build_mcp_server":
        return await handle_build_server_tool(arguments)
    
    else:
        return {"error": f"Unknown tool: {name}"}

async def handle_build_server_tool(arguments: dict):
    """Handle build_mcp_server tool calls"""
    platform = arguments.get("platform")
    description = arguments.get("description")
    
    # Validate required parameters
    if not all([platform, description]):
        return {"error": "platform and description are required"}
    
    # Get fixed public UUID
    user_uuid = get_user_uuid()
    
    # Assess API viability first
    assessment = await assess_platform_api(platform)
    
    if not assessment["viable"]:
        # Log feature request
        feature_request = {
            "user_uuid": user_uuid,
            "platform": platform,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "status": "feature_request"
        }
        
        # Save feature request (in real implementation, save to database)
        return {"text": f"Platform {platform} is not currently supported, but your request has been noted for future development."}
    
    # Determine next version number
    base_builds_path = Path(__file__).parent / "builds" / user_uuid / platform
    version = 1
    if base_builds_path.exists():
        existing_versions = [int(p.name) for p in base_builds_path.iterdir() if p.is_dir() and p.name.isdigit()]
        if existing_versions:
            version = max(existing_versions) + 1
    
    # Create build directory structure
    build_path = get_builds_path(user_uuid, platform, version)
    build_path.mkdir(parents=True, exist_ok=True)
    
    # Store build prompt and metadata
    prompt_data = {
        "platform": platform,
        "description": description,
        "user_uuid": user_uuid,
        "version": version,
        "timestamp": datetime.now().isoformat(),
        "public_access": True
    }
    
    with open(build_path / "prompt.txt", "w") as f:
        f.write(json.dumps(prompt_data, indent=2))
    
    # Trigger async pipeline
    try:
        from .pipeline import pipeline
        asyncio.create_task(pipeline.execute_build_pipeline(
            user_uuid=user_uuid,
            user_email="public@example.com",
            platform=platform,
            description=description,
            version=version
        ))
    except ImportError:
        # Pipeline not available, continue without it
        print(f"Build pipeline triggered for {user_uuid}/{platform}/v{version}")
    
    return {"text": f"MCP server build initiated for {platform}. Build ID: {user_uuid}/{platform}/v{version}. Build will be publicly accessible when deployment is complete."}

async def handle_mcp(request: Request):
    """Handle MCP protocol requests on /mcp endpoint"""
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                    },
                    "serverInfo": {
                        "name": "mcp-builder",
                        "version": "1.0.0"
                    }
                }
            }
            
        elif method == "tools/list":
            tools = get_available_tools()
            response = {
                "jsonrpc": "2.0", 
                "id": request_id,
                "result": {
                    "tools": tools
                }
            }
            
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            try:
                result = await handle_tool_call(tool_name, arguments)
                
                if "error" in result:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -1,
                            "message": result["error"]
                        }
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id, 
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": result.get("text", str(result))
                                }
                            ]
                        }
                    }
            except Exception as e:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -1,
                        "message": str(e)
                    }
                }
        else:
            response = {
                "jsonrpc": "2.0", 
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
            
        return JSONResponse(response)
        
    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": f"Parse error: {str(e)}"
            }
        }, status_code=400)

# Create Starlette app
app = Starlette(
    routes=[
        Route("/mcp", handle_mcp, methods=["POST"]),
    ]
)

# FastMCP expects these variable names for deployment
mcp = app  # FastMCP compatibility
server = app  # Alternative name

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
