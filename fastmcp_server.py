#!/usr/bin/env python3
"""
FastMCP Compatible MCP Builder Server
Designed for deployment on fastmcp.cloud
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Optional, Dict, List
from pathlib import Path
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# User management
user_db = {}  # email -> uuid mapping

# Platform viability cache
platform_cache = {}

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
    
    return {"viable": True, "oauth_required": True, "needs_research": True}

async def handle_viability_check(params: dict) -> dict:
    """Handle platform viability check requests"""
    platform = params.get("platform")
    user_email = params.get("user_email")
    
    if not platform or not user_email:
        return {
            "error": "platform and user_email are required"
        }
    
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
        
    return {
        "content": [{
            "type": "text", 
            "text": json.dumps(response, indent=2)
        }]
    }

async def handle_build_server(params: dict) -> dict:
    """Handle MCP server build requests"""
    platform = params.get("platform")
    user_email = params.get("user_email") 
    client_id = params.get("client_id")
    client_secret = params.get("client_secret")
    redirect_url = params.get("redirect_url")
    description = params.get("description")
    
    # Validate required parameters
    if not all([platform, user_email, client_id, client_secret, redirect_url, description]):
        return {
            "error": "All parameters are required (platform, user_email, client_id, client_secret, redirect_url, description)"
        }
    
    # Get user UUID
    user_uuid = get_user_uuid(user_email)
    
    # Assess API viability first
    assessment = await assess_platform_api(platform)
    
    if not assessment["viable"]:
        return {
            "content": [{
                "type": "text",
                "text": f"Platform {platform} is not currently supported, but your request has been noted for future development."
            }]
        }
    
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
    
    # For demo purposes, simulate pipeline execution
    # In production, this would trigger the actual pipeline
    print(f"Build pipeline triggered for {user_uuid}/{platform}/v{version}")
    
    return {
        "content": [{
            "type": "text",
            "text": f"MCP server build initiated for {platform}. Build ID: {user_uuid}/{platform}/v{version}. You will receive an email when deployment is complete."
        }]
    }

def get_available_tools() -> List[dict]:
    """Get list of available tools"""
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
                    },
                    "user_email": {
                        "type": "string", 
                        "description": "Email of the requesting user"
                    }
                },
                "required": ["platform", "user_email"]
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
                    "user_email": {
                        "type": "string",
                        "description": "Email of the requesting user"
                    },
                    "client_id": {
                        "type": "string",
                        "description": "OAuth Client ID"
                    },
                    "client_secret": {
                        "type": "string", 
                        "description": "OAuth Client Secret"
                    },
                    "redirect_url": {
                        "type": "string",
                        "description": "OAuth Redirect URL"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of what the MCP server should do"
                    }
                },
                "required": ["platform", "user_email", "client_id", "client_secret", "redirect_url", "description"]
            }
        }
    ]

class MCPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for FastMCP deployment"""
    
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length).decode('utf-8')
                request_data = json.loads(post_data)
            else:
                request_data = {}
            
            method = request_data.get('method', '')
            params = request_data.get('params', {})
            
            # Route requests
            if method == "tools/list":
                response = {
                    "tools": get_available_tools()
                }
            elif method == "tools/call":
                name = params.get("name", "")
                arguments = params.get("arguments", {})
                
                # Handle tool calls
                if name == "is_building_mcp_server_viable":
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    response = loop.run_until_complete(handle_viability_check(arguments))
                elif name == "build_mcp_server":
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    response = loop.run_until_complete(handle_build_server(arguments))
                else:
                    response = {
                        "content": [{
                            "type": "text",
                            "text": f"Unknown tool: {name}"
                        }]
                    }
            else:
                response = {"error": f"Unknown method: {method}"}
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {"error": str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests with basic info"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "service": "MCP Builder",
                "tools": len(get_available_tools())
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                "name": "MCP Builder Server",
                "version": "1.0.0",
                "description": "Builds MCP servers for various platforms",
                "tools": get_available_tools()
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def main():
    """Start the FastMCP server"""
    port = int(os.environ.get('PORT', 8000))
    
    print(f"Starting MCP Builder Server on port {port}")
    print("Available tools:")
    for tool in get_available_tools():
        print(f"  - {tool['name']}: {tool['description']}")
    
    # Create builds directory
    builds_dir = Path(__file__).parent / "builds"
    builds_dir.mkdir(exist_ok=True)
    
    httpd = HTTPServer(('0.0.0.0', port), MCPHandler)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()

if __name__ == "__main__":
    main()
