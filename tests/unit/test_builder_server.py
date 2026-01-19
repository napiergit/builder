#!/usr/bin/env python3
"""
Unit tests for MCP Builder Server
"""

import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

# Import the builder server
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "builder"))

from server import server, get_user_uuid, assess_platform_api


class TestBuilderServer:
    """Test MCP Builder Server functionality"""
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test that server lists correct tools"""
        tools = await server.list_tools()
        
        tool_names = [tool.name for tool in tools]
        assert "is_building_mcp_server_viable" in tool_names
        assert "build_mcp_server" in tool_names
        assert len(tools) == 2
    
    def test_get_user_uuid(self):
        """Test user UUID generation and persistence"""
        email = "test@example.com"
        
        # First call should create UUID
        uuid1 = get_user_uuid(email)
        assert uuid1 is not None
        assert len(uuid1) == 36  # Standard UUID length
        
        # Second call should return same UUID
        uuid2 = get_user_uuid(email)
        assert uuid1 == uuid2
        
        # Different email should get different UUID
        uuid3 = get_user_uuid("other@example.com")
        assert uuid3 != uuid1
    
    @pytest.mark.asyncio
    async def test_assess_platform_api_known(self):
        """Test API assessment for known platforms"""
        result = await assess_platform_api("github")
        
        assert result["viable"] is True
        assert result["oauth_required"] is True
        
        result = await assess_platform_api("gmail")
        assert result["viable"] is True
        assert result["oauth_required"] is True
    
    @pytest.mark.asyncio
    async def test_assess_platform_api_unknown(self):
        """Test API assessment for unknown platforms"""
        result = await assess_platform_api("unknown_platform")
        
        assert result["viable"] is True  # Unknown platforms are treated as potentially viable
        assert result["oauth_required"] is True
        assert result.get("needs_research") is True
    
    @pytest.mark.asyncio
    async def test_viability_tool_success(self):
        """Test viability tool with valid parameters"""
        result = await server.call_tool("is_building_mcp_server_viable", {
            "platform": "github",
            "user_email": "test@example.com"
        })
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        
        assert response_data["viable"] is True
        assert "required_parameters" in response_data
        assert "oauth_credentials" in response_data["required_parameters"]
    
    @pytest.mark.asyncio
    async def test_viability_tool_missing_params(self):
        """Test viability tool with missing parameters"""
        result = await server.call_tool("is_building_mcp_server_viable", {
            "platform": "github"
            # Missing user_email
        })
        
        assert len(result) == 1
        assert "Error" in result[0].text
        assert "required" in result[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_build_tool_success(self):
        """Test build tool with valid parameters"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the builds directory
            with patch('pathlib.Path.__truediv__') as mock_path:
                mock_build_path = MagicMock()
                mock_build_path.mkdir = MagicMock()
                mock_build_path.__truediv__ = MagicMock(return_value=MagicMock())
                mock_path.return_value = mock_build_path
                
                result = await server.call_tool("build_mcp_server", {
                    "platform": "github",
                    "user_email": "test@example.com",
                    "client_id": "test_client_id",
                    "client_secret": "test_secret",
                    "redirect_url": "http://localhost:8080/callback",
                    "description": "Test MCP server for GitHub"
                })
                
                assert len(result) == 1
                assert "build initiated" in result[0].text.lower()
                assert "github" in result[0].text
    
    @pytest.mark.asyncio 
    async def test_build_tool_missing_params(self):
        """Test build tool with missing parameters"""
        result = await server.call_tool("build_mcp_server", {
            "platform": "github",
            "user_email": "test@example.com"
            # Missing other required parameters
        })
        
        assert len(result) == 1
        assert "Error" in result[0].text
        assert "required" in result[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_build_tool_unsupported_platform(self):
        """Test build tool with unsupported platform"""
        # Mock assess_platform_api to return not viable
        with patch('server.assess_platform_api') as mock_assess:
            mock_assess.return_value = {"viable": False}
            
            result = await server.call_tool("build_mcp_server", {
                "platform": "unsupported_platform",
                "user_email": "test@example.com", 
                "client_id": "test_client_id",
                "client_secret": "test_secret",
                "redirect_url": "http://localhost:8080/callback",
                "description": "Test description"
            })
            
            assert len(result) == 1
            assert "not currently supported" in result[0].text
            assert "noted for future development" in result[0].text
    
    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        """Test calling unknown tool"""
        result = await server.call_tool("nonexistent_tool", {})
        
        assert len(result) == 1
        assert "Unknown tool" in result[0].text


class TestVersionManagement:
    """Test version management functionality"""
    
    @pytest.mark.asyncio
    async def test_version_increment(self):
        """Test that versions increment correctly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock directory structure
            user_uuid = "test-uuid-123"
            platform = "github"
            
            base_path = Path(temp_dir) / user_uuid / platform
            
            # Create version 1
            v1_path = base_path / "1"
            v1_path.mkdir(parents=True)
            
            # Create version 2  
            v2_path = base_path / "2"
            v2_path.mkdir(parents=True)
            
            # Mock get_builds_path to use temp directory
            with patch('server.get_builds_path') as mock_get_path:
                mock_get_path.return_value = base_path / "3"  # Next version should be 3
                
                # The build logic should detect existing versions and increment
                # This would be tested in integration test with actual build call


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
