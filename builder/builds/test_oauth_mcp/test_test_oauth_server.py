#!/usr/bin/env python3
"""
Test suite for test_oauth MCP Server
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock

# Import the server module (adjust import path as needed)
import sys
import os
sys.path.append(os.path.dirname(__file__))

from test_oauth_mcp_server import server, oauth, OAuthManager

class TestOAuth:
    """Test OAuth functionality"""
    
    def test_get_auth_url(self):
        """Test OAuth URL generation"""
        auth_manager = OAuthManager()
        url = auth_manager.get_auth_url()
        
        assert "client_id=your_oauth_client_id" in url
        assert "redirect_uri=http://localhost:8080/callback" in url
        assert "response_type=code" in url
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token(self):
        """Test token exchange"""
        auth_manager = OAuthManager()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "test_token",
            "token_type": "Bearer"
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await auth_manager.exchange_code_for_token("test_code")
            
            assert result["access_token"] == "test_token"
    
    @pytest.mark.asyncio
    async def test_api_request_without_token(self):
        """Test API request fails without token"""
        auth_manager = OAuthManager()
        
        with pytest.raises(ValueError, match="Not authenticated"):
            await auth_manager.make_api_request("/test")

class TestMCPServer:
    """Test MCP server functionality"""
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test tool listing"""
        tools = await server.list_tools()
        
        tool_names = [tool.name for tool in tools]
        assert "authenticate" in tool_names
        assert "complete_auth" in tool_names
        assert "get_user_info" in tool_names
    
    @pytest.mark.asyncio
    async def test_authenticate_tool(self):
        """Test authenticate tool call"""
        result = await server.call_tool("authenticate", {})
        
        assert len(result) == 1
        assert "Please visit this URL" in result[0].text
        assert "your_oauth_client_id" in result[0].text
    
    @pytest.mark.asyncio
    async def test_complete_auth_missing_code(self):
        """Test auth completion without code"""
        result = await server.call_tool("complete_auth", {})
        
        assert len(result) == 1
        assert "Error: Authorization code is required" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_user_info_not_authenticated(self):
        """Test user info request without authentication"""
        # Reset oauth state
        oauth.access_token = None
        
        result = await server.call_tool("get_user_info", {})
        
        assert len(result) == 1
        assert "Please authenticate first" in result[0].text
    
    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        """Test unknown tool call"""
        result = await server.call_tool("nonexistent_tool", {})
        
        assert len(result) == 1
        assert "Unknown tool: nonexistent_tool" in result[0].text

class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_auth_flow(self):
        """Test complete authentication flow"""
        # Mock the token exchange
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "integration_test_token",
            "token_type": "Bearer"
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            # Complete authentication
            result = await server.call_tool("complete_auth", {"code": "test_code"})
            
            assert "Authentication successful" in result[0].text
            assert oauth.access_token == "integration_test_token"

def run_tests():
    """Run all tests"""
    pytest.main([__file__, "-v"])

if __name__ == "__main__":
    run_tests()
