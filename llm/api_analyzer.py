#!/usr/bin/env python3
"""
API Analyzer - Discovers and analyzes platform APIs for MCP server generation
"""

import asyncio
import json
import re
from typing import Dict, Any, List, Optional
import httpx
from dataclasses import dataclass


@dataclass
class APIEndpoint:
    """Represents a discovered API endpoint"""
    method: str
    path: str
    description: str
    parameters: Dict[str, Any]
    response_schema: Dict[str, Any]
    authentication_required: bool


class APIAnalyzer:
    """Analyzes platform APIs to understand capabilities and structure"""
    
    def __init__(self):
        self.known_platforms = {
            "github": {
                "base_url": "https://api.github.com",
                "oauth_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
                "scopes": ["repo", "user", "gist"],
                "documentation": "https://docs.github.com/en/rest"
            },
            "gmail": {
                "base_url": "https://gmail.googleapis.com",
                "oauth_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "scopes": ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"],
                "documentation": "https://developers.google.com/gmail/api"
            },
            "slack": {
                "base_url": "https://slack.com/api",
                "oauth_url": "https://slack.com/oauth/v2/authorize",
                "token_url": "https://slack.com/api/oauth.v2.access",
                "scopes": ["channels:read", "chat:write", "users:read"],
                "documentation": "https://api.slack.com"
            },
            "notion": {
                "base_url": "https://api.notion.com/v1",
                "oauth_url": "https://api.notion.com/v1/oauth/authorize",
                "token_url": "https://api.notion.com/v1/oauth/token",
                "scopes": ["read", "write"],
                "documentation": "https://developers.notion.com"
            },
            "twitter": {
                "base_url": "https://api.twitter.com/2",
                "oauth_url": "https://twitter.com/i/oauth2/authorize",
                "token_url": "https://api.twitter.com/2/oauth2/token",
                "scopes": ["tweet.read", "tweet.write", "users.read"],
                "documentation": "https://developer.twitter.com/en/docs/twitter-api"
            }
        }
    
    async def analyze_platform(self, platform: str) -> Dict[str, Any]:
        """Analyze a platform's API capabilities"""
        
        platform_lower = platform.lower()
        
        if platform_lower in self.known_platforms:
            # Use known platform configuration
            platform_config = self.known_platforms[platform_lower]
            
            # Discover endpoints
            endpoints = await self._discover_endpoints(platform_config)
            
            # Analyze authentication requirements
            auth_info = self._analyze_authentication(platform_config)
            
            # Generate recommended tools
            recommended_tools = self._generate_recommended_tools(platform_lower, endpoints)
            
            return {
                "platform": platform,
                "base_url": platform_config["base_url"],
                "authentication": auth_info,
                "endpoints": endpoints,
                "recommended_tools": recommended_tools,
                "capabilities": self._assess_capabilities(endpoints),
                "rate_limits": self._get_rate_limits(platform_lower),
                "known_platform": True
            }
        else:
            # Unknown platform - try to discover
            return await self._analyze_unknown_platform(platform)
    
    async def _discover_endpoints(self, platform_config: Dict[str, str]) -> List[APIEndpoint]:
        """Discover API endpoints for known platforms"""
        
        # This would typically involve:
        # 1. Fetching OpenAPI/Swagger documentation
        # 2. Parsing API documentation
        # 3. Making discovery requests to well-known endpoints
        
        # For now, returning platform-specific endpoint knowledge
        platform_name = platform_config["base_url"].split("//")[1].split(".")[0]
        
        if "github" in platform_name:
            return [
                APIEndpoint(
                    method="GET",
                    path="/user",
                    description="Get authenticated user information",
                    parameters={},
                    response_schema={"login": "string", "name": "string", "email": "string"},
                    authentication_required=True
                ),
                APIEndpoint(
                    method="GET", 
                    path="/user/repos",
                    description="List user repositories",
                    parameters={"type": "string", "sort": "string"},
                    response_schema={"type": "array", "items": {"name": "string", "description": "string"}},
                    authentication_required=True
                ),
                APIEndpoint(
                    method="POST",
                    path="/user/repos", 
                    description="Create a new repository",
                    parameters={"name": "string", "description": "string", "private": "boolean"},
                    response_schema={"id": "number", "name": "string", "clone_url": "string"},
                    authentication_required=True
                ),
                APIEndpoint(
                    method="GET",
                    path="/repos/{owner}/{repo}/issues",
                    description="List repository issues",
                    parameters={"state": "string", "labels": "string"},
                    response_schema={"type": "array", "items": {"number": "number", "title": "string"}},
                    authentication_required=True
                ),
                APIEndpoint(
                    method="POST",
                    path="/repos/{owner}/{repo}/issues",
                    description="Create a new issue",
                    parameters={"title": "string", "body": "string", "labels": "array"},
                    response_schema={"number": "number", "title": "string", "html_url": "string"},
                    authentication_required=True
                )
            ]
        
        elif "gmail" in platform_name or "google" in platform_name:
            return [
                APIEndpoint(
                    method="GET",
                    path="/gmail/v1/users/me/profile",
                    description="Get user profile",
                    parameters={},
                    response_schema={"emailAddress": "string", "messagesTotal": "number"},
                    authentication_required=True
                ),
                APIEndpoint(
                    method="GET",
                    path="/gmail/v1/users/me/messages",
                    description="List messages",
                    parameters={"q": "string", "maxResults": "number"},
                    response_schema={"messages": "array", "resultSizeEstimate": "number"},
                    authentication_required=True
                ),
                APIEndpoint(
                    method="POST",
                    path="/gmail/v1/users/me/messages/send",
                    description="Send an email",
                    parameters={"raw": "string"},
                    response_schema={"id": "string", "labelIds": "array"},
                    authentication_required=True
                )
            ]
        
        elif "slack" in platform_name:
            return [
                APIEndpoint(
                    method="GET",
                    path="/auth.test",
                    description="Test authentication",
                    parameters={},
                    response_schema={"ok": "boolean", "user": "string"},
                    authentication_required=True
                ),
                APIEndpoint(
                    method="GET",
                    path="/conversations.list",
                    description="List channels",
                    parameters={"types": "string", "limit": "number"},
                    response_schema={"channels": "array", "ok": "boolean"},
                    authentication_required=True
                ),
                APIEndpoint(
                    method="POST",
                    path="/chat.postMessage",
                    description="Post message to channel",
                    parameters={"channel": "string", "text": "string"},
                    response_schema={"ok": "boolean", "ts": "string"},
                    authentication_required=True
                )
            ]
        
        else:
            # Generic discovery for other platforms
            return []
    
    def _analyze_authentication(self, platform_config: Dict[str, str]) -> Dict[str, Any]:
        """Analyze authentication requirements"""
        
        return {
            "type": "oauth2",
            "oauth_url": platform_config.get("oauth_url"),
            "token_url": platform_config.get("token_url"),
            "required_scopes": platform_config.get("scopes", []),
            "token_type": "Bearer",
            "refresh_token_supported": True
        }
    
    def _generate_recommended_tools(self, platform: str, endpoints: List[APIEndpoint]) -> List[Dict[str, Any]]:
        """Generate recommended MCP tools based on discovered endpoints"""
        
        tools = []
        
        for endpoint in endpoints:
            tool_name = self._endpoint_to_tool_name(endpoint.path, endpoint.method)
            
            tools.append({
                "name": tool_name,
                "description": endpoint.description,
                "method": endpoint.method,
                "endpoint": endpoint.path,
                "parameters": endpoint.parameters,
                "response_schema": endpoint.response_schema
            })
        
        return tools
    
    def _endpoint_to_tool_name(self, path: str, method: str) -> str:
        """Convert API endpoint to MCP tool name"""
        
        # Remove path parameters and clean up
        clean_path = re.sub(r'\{[^}]+\}', '', path)
        path_parts = [part for part in clean_path.split('/') if part]
        
        # Generate meaningful tool names
        if method.upper() == "GET":
            if len(path_parts) == 1:
                return f"get_{path_parts[0]}"
            else:
                return f"list_{path_parts[-1]}"
        elif method.upper() == "POST":
            return f"create_{path_parts[-1]}"
        elif method.upper() == "PUT" or method.upper() == "PATCH":
            return f"update_{path_parts[-1]}"
        elif method.upper() == "DELETE":
            return f"delete_{path_parts[-1]}"
        else:
            return f"{method.lower()}_{path_parts[-1]}"
    
    def _assess_capabilities(self, endpoints: List[APIEndpoint]) -> Dict[str, Any]:
        """Assess platform capabilities based on endpoints"""
        
        capabilities = {
            "read_operations": 0,
            "write_operations": 0,
            "supports_search": False,
            "supports_webhooks": False,
            "supports_real_time": False
        }
        
        for endpoint in endpoints:
            if endpoint.method.upper() == "GET":
                capabilities["read_operations"] += 1
            elif endpoint.method.upper() in ["POST", "PUT", "PATCH", "DELETE"]:
                capabilities["write_operations"] += 1
            
            if "search" in endpoint.path or "query" in endpoint.description.lower():
                capabilities["supports_search"] = True
        
        return capabilities
    
    def _get_rate_limits(self, platform: str) -> Dict[str, Any]:
        """Get known rate limits for platform"""
        
        rate_limits = {
            "github": {"requests_per_hour": 5000, "requests_per_minute": 60},
            "gmail": {"requests_per_day": 1000000000, "requests_per_second": 250},
            "slack": {"requests_per_minute": 50, "burst_requests": 100},
            "notion": {"requests_per_second": 3, "requests_per_minute": 100},
            "twitter": {"requests_per_15_min": 300, "requests_per_day": 500000}
        }
        
        return rate_limits.get(platform, {"unknown": True})
    
    async def _analyze_unknown_platform(self, platform: str) -> Dict[str, Any]:
        """Attempt to analyze an unknown platform"""
        
        # This would involve:
        # 1. Web scraping documentation
        # 2. Looking for OpenAPI specs
        # 3. Making test requests to common endpoints
        
        return {
            "platform": platform,
            "known_platform": False,
            "analysis_status": "requires_manual_review",
            "recommendations": [
                "Check for API documentation",
                "Look for OAuth endpoints",
                "Verify CORS policy",
                "Test common REST patterns"
            ]
        }
