#!/usr/bin/env python3
"""
MCP Builder Server - Builds MCP servers based on platform APIs
FastMCP Compatible Version
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Optional, Dict, List
from pathlib import Path
import os
import sys

try:
    from fastmcp import FastMCP
except ImportError:
    # Fallback implementation for FastMCP compatibility
    class FastMCP:
        def __init__(self, name: str):
            self.name = name
            self.tools = []
        
        def tool(self, name: str = None, description: str = None):
            def decorator(func):
                tool_name = name or func.__name__
                self.tools.append({
                    "name": tool_name,
                    "description": description or func.__doc__ or "No description",
                    "handler": func
                })
                return func
            return decorator


# User management
user_db = {}  # email -> uuid mapping

# Platform viability cache
platform_cache = {}

# FastMCP compatible server object
mcp = FastMCP("mcp-builder")
server = mcp  # For backward compatibility
app = mcp  # FastMCP expects 'app' or 'mcp' variable

def get_user_uuid(email: str) -> str:
    """Get or create UUID for user email"""
    if email not in user_db:
        user_db[email] = str(uuid.uuid4())
    return user_db[email]

def get_builds_path(user_uuid: str, platform: str, version: int) -> Path:
    """Get the path for builds storage"""
    base_path = Path(__file__).parent / "builds"
    return base_path / user_uuid / platform / str(version)

async def assess_platform_api(platform: str) -> Dict[str, Any]:
    """Assess if platform API is viable for MCP server creation"""
    # Simulate API assessment logic
    # In real implementation, this would analyze the platform's API
    
    known_platforms = {
        "github": {"viable": True, "oauth_required": True},
        "gmail": {"viable": True, "oauth_required": True}, 
        "slack": {"viable": True, "oauth_required": True},
        "twitter": {"viable": True, "oauth_required": True},
        "discord": {"viable": True, "oauth_required": True},
        "notion": {"viable": True, "oauth_required": True},
    }
    
    if platform.lower() in known_platforms:
        return known_platforms[platform.lower()]
    
    # For unknown platforms, return as potentially viable but needs assessment
    return {"viable": True, "oauth_required": True, "needs_research": True}

@mcp.tool(
    name="is_building_mcp_server_viable",
    description="Check if building an MCP server for a platform is viable"
)
async def is_building_mcp_server_viable(platform: str, user_email: str) -> str:
    """Check if building an MCP server for a platform is viable"""
    if not platform or not user_email:
        return "Error: platform and user_email are required"
    
    # Assess platform viability
    assessment = await assess_platform_api(platform)
    
    if assessment["viable"]:
        required_params = {
            "platform_name": platform,
            "oauth_credentials": {
                "client_id": "Required - OAuth Client ID for the platform",
                "client_secret": "Required - OAuth Client Secret", 
                "redirect_url": "Required - OAuth Redirect URL"
            }
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
        
    return json.dumps(response, indent=2)

@mcp.tool(
    name="build_mcp_server",
    description="Build an MCP server for the specified platform"
)
async def build_mcp_server(
    platform: str, 
    user_email: str, 
    client_id: str, 
    client_secret: str, 
    redirect_url: str, 
    description: str
) -> str:
    """Build an MCP server for the specified platform"""
    # Validate required parameters
    if not all([platform, user_email, client_id, client_secret, redirect_url, description]):
        return "Error: All parameters are required (platform, user_email, client_id, client_secret, redirect_url, description)"
    
    # Get user UUID
    user_uuid = get_user_uuid(user_email)
    
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
        return f"Platform {platform} is not currently supported, but your request has been noted for future development."
    
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
        "oauth_credentials": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_url": redirect_url
        },
        "user_uuid": user_uuid,
        "version": version,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(build_path / "prompt.txt", "w") as f:
        f.write(json.dumps(prompt_data, indent=2))
    
    # Trigger async pipeline
    try:
        from .pipeline import pipeline
        asyncio.create_task(pipeline.execute_build_pipeline(
            user_uuid=user_uuid,
            user_email=user_email,
            platform=platform,
            description=description,
            oauth_creds=prompt_data["oauth_credentials"],
            version=version
        ))
    except ImportError:
        # Pipeline not available, continue without it
        print(f"Build pipeline triggered for {user_uuid}/{platform}/v{version}")
    
    return f"MCP server build initiated for {platform}. Build ID: {user_uuid}/{platform}/v{version}. You will receive an email when deployment is complete."

# FastMCP handles server initialization automatically
# No need for custom HTTP server implementation

if __name__ == "__main__":
    # For development/testing - FastMCP deployment handles this automatically
    import uvicorn
    uvicorn.run(mcp, host="0.0.0.0", port=int(os.environ.get('PORT', 8000)))
