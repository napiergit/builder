#!/usr/bin/env python3
"""
LLM Code Generator with Guardrails for MCP Servers
"""

import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile
import subprocess

from api_analyzer import APIAnalyzer
from guardrails import GuardrailsEngine
from validator import CodeValidator


class CodeGenerator:
    """Generates MCP server code using LLM with safety guardrails"""
    
    def __init__(self, llm_endpoint: Optional[str] = None):
        self.llm_endpoint = llm_endpoint or os.getenv("LLM_ENDPOINT", "http://localhost:11434")
        self.api_analyzer = APIAnalyzer()
        self.guardrails = GuardrailsEngine()
        self.validator = CodeValidator()
        
    async def generate_mcp_server(
        self,
        platform: str,
        description: str,
        oauth_creds: Dict[str, str],
        user_uuid: str,
        version: int,
        previous_versions: List[Dict] = None
    ) -> Dict[str, Any]:
        """Generate complete MCP server implementation"""
        
        # Step 1: Analyze platform API
        print(f"Analyzing {platform} API...")
        api_info = await self.api_analyzer.analyze_platform(platform)
        
        # Step 2: Load cookie cutter template
        template_path = Path(__file__).parent.parent / "cookiecutter"
        template_code = self._load_template(template_path)
        
        # Step 3: Build generation prompt with guardrails
        prompt = self._build_generation_prompt(
            platform=platform,
            description=description,
            api_info=api_info,
            template_code=template_code,
            oauth_creds=oauth_creds,
            previous_versions=previous_versions
        )
        
        # Step 4: Generate code with iterative improvement
        max_attempts = 3
        for attempt in range(max_attempts):
            print(f"Generation attempt {attempt + 1}/{max_attempts}")
            
            # Generate code using LLM
            generated_code = await self._call_llm(prompt)
            
            # Apply guardrails
            validated_code = self.guardrails.validate_and_sanitize(generated_code)
            
            # Test the generated code
            test_results = await self.validator.validate_code(
                validated_code, platform, oauth_creds
            )
            
            if test_results["passed"]:
                print("Code generation successful!")
                return {
                    "success": True,
                    "code": validated_code,
                    "test_results": test_results,
                    "attempt": attempt + 1
                }
            else:
                print(f"Tests failed on attempt {attempt + 1}")
                # Add test feedback to prompt for next iteration
                prompt = self._enhance_prompt_with_feedback(prompt, test_results)
        
        return {
            "success": False,
            "error": "Code generation failed after maximum attempts",
            "last_attempt": validated_code,
            "test_results": test_results
        }
    
    def _load_template(self, template_path: Path) -> Dict[str, str]:
        """Load cookie cutter template files"""
        template_files = {}
        
        for file_path in template_path.glob("*.py"):
            if not file_path.name.startswith("test_"):
                with open(file_path, 'r') as f:
                    template_files[file_path.name] = f.read()
        
        return template_files
    
    def _build_generation_prompt(
        self,
        platform: str,
        description: str,
        api_info: Dict,
        template_code: Dict[str, str],
        oauth_creds: Dict[str, str],
        previous_versions: List[Dict] = None
    ) -> str:
        """Build comprehensive prompt for LLM code generation"""
        
        prompt = f"""You are an expert MCP (Model Context Protocol) server developer. Generate a complete, production-ready MCP server for the {platform} platform.

REQUIREMENTS:
- Platform: {platform}
- Description: {description}
- OAuth Client ID: {oauth_creds['client_id']}
- OAuth Secret: {oauth_creds['client_secret']}
- Redirect URL: {oauth_creds['redirect_url']}

API INFORMATION:
{json.dumps(api_info, indent=2)}

TEMPLATE TO FOLLOW:
Use this template structure and modify it for {platform}:

{template_code.get('{{cookiecutter.platform_name}}_mcp_server.py', '')}

GUARDRAILS AND REQUIREMENTS:
1. SECURITY: Never expose OAuth secrets in logs or responses
2. ERROR HANDLING: Always wrap API calls in proper try/catch blocks
3. AUTHENTICATION: Implement proper OAuth flow with token refresh
4. RATE LIMITING: Respect platform API rate limits
5. TESTING: Code must be testable with the provided test framework
6. MCP COMPLIANCE: Follow MCP protocol specifications exactly
7. DOCUMENTATION: Add clear docstrings for all functions

PLATFORM-SPECIFIC REQUIREMENTS:
- Use the correct API endpoints for {platform}
- Implement appropriate scopes for OAuth
- Handle platform-specific error responses
- Support the most useful {platform} operations

"""

        if previous_versions:
            prompt += "\nPREVIOUS VERSIONS TO IMPROVE UPON:\n"
            for i, version in enumerate(previous_versions):
                prompt += f"Version {i+1}: {version.get('feedback', '')}\n"

        prompt += """
OUTPUT REQUIREMENTS:
1. Complete Python file that can be run directly
2. All imports at the top
3. Working OAuth implementation
4. At least 5 useful tools for the platform
5. Proper error handling and logging
6. Code that passes the test suite

Generate the complete MCP server code now:
"""
        
        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM service to generate code"""
        # This would integrate with your chosen LLM service
        # For now, simulating with a placeholder
        
        # In real implementation, this would be:
        # - OpenAI API call
        # - Anthropic Claude API
        # - Local Ollama instance
        # - AWS Bedrock
        # etc.
        
        try:
            # Placeholder for actual LLM integration
            # This is where you'd make the HTTP request to your LLM service
            
            # Simulated response for demo purposes
            simulated_response = self._generate_placeholder_code()
            return simulated_response
            
        except Exception as e:
            raise Exception(f"LLM call failed: {str(e)}")
    
    def _generate_placeholder_code(self) -> str:
        """Generate placeholder code for demonstration"""
        return '''#!/usr/bin/env python3
"""
Generated MCP Server with OAuth
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
CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET") 
REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI")

server = Server("generated-mcp")

class OAuthManager:
    def __init__(self):
        self.access_token: Optional[str] = None
    
    def get_auth_url(self) -> str:
        params = {
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'response_type': 'code',
            'scope': 'read write'
        }
        return f"https://platform.com/oauth/authorize?{urlencode(params)}"

oauth = OAuthManager()

@server.list_tools()
async def list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="authenticate",
            description="Start OAuth authentication",
            inputSchema={"type": "object", "properties": {}, "required": []}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    if name == "authenticate":
        return [types.TextContent(type="text", text="Generated code placeholder")]
    return [types.TextContent(type="text", text="Unknown tool")]

async def main():
    async with stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    def _enhance_prompt_with_feedback(self, original_prompt: str, test_results: Dict) -> str:
        """Enhance prompt with test feedback for next iteration"""
        
        feedback = f"""
PREVIOUS ATTEMPT FAILED WITH THESE ISSUES:
{json.dumps(test_results.get('failures', []), indent=2)}

SPECIFIC ERRORS TO FIX:
{test_results.get('error_details', 'No specific error details')}

Please fix these issues in the next generation:
"""
        
        return original_prompt + feedback
