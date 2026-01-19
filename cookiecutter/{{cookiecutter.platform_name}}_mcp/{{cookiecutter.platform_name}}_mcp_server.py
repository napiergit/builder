#!/usr/bin/env python3
"""
{{cookiecutter.platform_name}} MCP Server
{{cookiecutter.server_description}}
"""

import asyncio
import json
import os
from typing import Any, Optional, Dict, List
from urllib.parse import urlencode
import httpx

from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# OAuth Configuration
CLIENT_ID = "{{cookiecutter.client_id}}"
CLIENT_SECRET = "{{cookiecutter.client_secret}}" 
REDIRECT_URI = "{{cookiecutter.redirect_url}}"

# Platform API Configuration
BASE_URL = "https://api.{{cookiecutter.platform_name}}.com"  # Adjust per platform

server = Server("{{cookiecutter.platform_name}}-mcp")

class OAuthManager:
    """Handles OAuth authentication flow"""
    
    def __init__(self):
        self.access_token: Optional[str] = None
    
    def get_auth_url(self) -> str:
        """Generate OAuth authorization URL"""
        params = {
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'response_type': 'code',
            'scope': 'read write'  # Adjust scopes per platform
        }
        
        auth_base = f"https://{{cookiecutter.platform_name}}.com/oauth/authorize"  # Adjust per platform
        return f"{auth_base}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/oauth/token",  # Adjust endpoint per platform
                data={
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'code': code,
                    'redirect_uri': REDIRECT_URI,
                    'grant_type': 'authorization_code'
                }
            )
            return response.json()
    
    async def make_api_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated API request"""
        if not self.access_token:
            raise ValueError("Not authenticated - call authenticate first")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(f"{BASE_URL}{endpoint}", headers=headers)
            elif method == "POST":
                response = await client.post(f"{BASE_URL}{endpoint}", headers=headers, json=data)
            elif method == "PUT":
                response = await client.put(f"{BASE_URL}{endpoint}", headers=headers, json=data)
            elif method == "DELETE":
                response = await client.delete(f"{BASE_URL}{endpoint}", headers=headers)
            
            response.raise_for_status()
            return response.json()

# Global OAuth manager
oauth = OAuthManager()

@server.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available tools for {{cookiecutter.platform_name}}"""
    return [
        types.Tool(
            name="authenticate",
            description="Start OAuth authentication flow",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="complete_auth",
            description="Complete OAuth flow with authorization code",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Authorization code from OAuth callback"
                    }
                },
                "required": ["code"]
            }
        ),
        # Add platform-specific tools here
        types.Tool(
            name="get_user_info",
            description="Get authenticated user information",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls"""
    
    try:
        if name == "authenticate":
            auth_url = oauth.get_auth_url()
            return [types.TextContent(
                type="text",
                text=f"Please visit this URL to authorize: {auth_url}"
            )]
        
        elif name == "complete_auth":
            code = arguments.get("code")
            if not code:
                return [types.TextContent(
                    type="text",
                    text="Error: Authorization code is required"
                )]
            
            token_data = await oauth.exchange_code_for_token(code)
            oauth.access_token = token_data.get("access_token")
            
            return [types.TextContent(
                type="text",
                text="Authentication successful! You can now use {{cookiecutter.platform_name}} tools."
            )]
        
        elif name == "get_user_info":
            if not oauth.access_token:
                return [types.TextContent(
                    type="text",
                    text="Error: Please authenticate first using the 'authenticate' tool"
                )]
            
            user_data = await oauth.make_api_request("/user")  # Adjust endpoint per platform
            return [types.TextContent(
                type="text",
                text=json.dumps(user_data, indent=2)
            )]
        
        # Add more platform-specific tools here
        
        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]

async def main():
    """Main server entry point"""
    async with stdio_server() as streams:
        await server.run(
            streams[0], streams[1], server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
