#!/usr/bin/env python3
"""
Integration tests for the complete build pipeline
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from llm.code_generator import CodeGenerator
from llm.api_analyzer import APIAnalyzer
from llm.guardrails import GuardrailsEngine
from llm.validator import CodeValidator


class TestBuildPipeline:
    """Integration tests for the complete build pipeline"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_generation(self):
        """Test complete code generation pipeline"""
        generator = CodeGenerator()
        
        # Mock LLM call to avoid external dependency
        with patch.object(generator, '_call_llm') as mock_llm:
            mock_llm.return_value = self._get_valid_test_code()
            
            result = await generator.generate_mcp_server(
                platform="github",
                description="Test GitHub MCP server",
                oauth_creds={
                    "client_id": "test_client_id",
                    "client_secret": "test_secret", 
                    "redirect_url": "http://localhost:8080/callback"
                },
                user_uuid="test-uuid-123",
                version=1
            )
            
            assert result["success"] is True
            assert "code" in result
            assert result["test_results"]["passed"] is True
    
    @pytest.mark.asyncio
    async def test_api_analyzer_integration(self):
        """Test API analyzer with code generator integration"""
        analyzer = APIAnalyzer()
        generator = CodeGenerator()
        
        # Test GitHub analysis
        api_info = await analyzer.analyze_platform("github")
        
        assert api_info["known_platform"] is True
        assert "endpoints" in api_info
        assert "recommended_tools" in api_info
        assert len(api_info["recommended_tools"]) > 0
        
        # Verify recommended tools are sensible
        tool_names = [tool["name"] for tool in api_info["recommended_tools"]]
        assert any("user" in name for name in tool_names)
        assert any("repo" in name for name in tool_names)
    
    def test_guardrails_integration(self):
        """Test guardrails with realistic code samples"""
        guardrails = GuardrailsEngine()
        
        # Test valid code
        valid_code = self._get_valid_test_code()
        violations = guardrails.check_violations(valid_code)
        critical_violations = [v for v in violations if v.severity == "error"]
        assert len(critical_violations) == 0
        
        # Test code with violations
        invalid_code = '''
import subprocess
CLIENT_SECRET = "hardcoded_secret_123"
eval("malicious_code")
        '''
        violations = guardrails.check_violations(invalid_code)
        critical_violations = [v for v in violations if v.severity == "error"]
        assert len(critical_violations) > 0
    
    @pytest.mark.asyncio
    async def test_validator_integration(self):
        """Test code validator with generated code"""
        validator = CodeValidator()
        
        valid_code = self._get_valid_test_code()
        result = await validator.validate_code(
            valid_code, 
            "github",
            {"client_id": "test", "client_secret": "test", "redirect_url": "test"}
        )
        
        assert result["syntax_valid"] is True
        assert result["mcp_compliance"] is True
        assert result["oauth_implementation"] is True
    
    @pytest.mark.asyncio
    async def test_pipeline_with_iterations(self):
        """Test pipeline with multiple iterations for improvement"""
        generator = CodeGenerator()
        
        # Mock LLM to fail first attempt, succeed second
        call_count = 0
        def mock_llm_call(prompt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "invalid python code {{{"  # Invalid syntax
            else:
                return self._get_valid_test_code()
        
        with patch.object(generator, '_call_llm', side_effect=mock_llm_call):
            result = await generator.generate_mcp_server(
                platform="github",
                description="Test server",
                oauth_creds={
                    "client_id": "test",
                    "client_secret": "test",
                    "redirect_url": "test"
                },
                user_uuid="test-uuid",
                version=1
            )
            
            # Should succeed on second attempt
            assert result["success"] is True
            assert result["attempt"] == 2
    
    def _get_valid_test_code(self):
        """Return valid MCP server code for testing"""
        return '''#!/usr/bin/env python3
import asyncio
import os
from typing import Any, Dict, List
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET") 
REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI")

server = Server("test-mcp")

class OAuthManager:
    def __init__(self):
        self.access_token = None
    
    def get_auth_url(self):
        return f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}"

oauth = OAuthManager()

@server.list_tools()
async def list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="authenticate",
            description="Start OAuth authentication",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="get_user_info",
            description="Get user information",
            inputSchema={
                "type": "object", 
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    try:
        if name == "authenticate":
            auth_url = oauth.get_auth_url()
            return [types.TextContent(type="text", text=f"Visit: {auth_url}")]
        elif name == "get_user_info":
            return [types.TextContent(type="text", text="User info placeholder")]
        else:
            return [types.TextContent(type="text", text="Unknown tool")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
'''


class TestErrorHandling:
    """Test error handling in integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_llm_service_failure(self):
        """Test handling when LLM service is unavailable"""
        generator = CodeGenerator()
        
        with patch.object(generator, '_call_llm') as mock_llm:
            mock_llm.side_effect = Exception("LLM service unavailable")
            
            result = await generator.generate_mcp_server(
                platform="github",
                description="Test",
                oauth_creds={"client_id": "test", "client_secret": "test", "redirect_url": "test"},
                user_uuid="test",
                version=1
            )
            
            assert result["success"] is False
            assert "LLM service unavailable" in str(result.get("error", ""))
    
    @pytest.mark.asyncio
    async def test_unknown_platform_handling(self):
        """Test handling of completely unknown platforms"""
        analyzer = APIAnalyzer()
        
        result = await analyzer.analyze_platform("completely_unknown_platform_xyz")
        
        assert result["known_platform"] is False
        assert result["analysis_status"] == "requires_manual_review"
        assert "recommendations" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
