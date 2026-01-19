#!/usr/bin/env python3
"""
Code Validator - Tests generated MCP server code for correctness and functionality
"""

import asyncio
import subprocess
import tempfile
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import importlib.util
import ast


class CodeValidator:
    """Validates generated MCP server code through multiple testing strategies"""
    
    def __init__(self):
        self.test_timeout = 30  # seconds
        
    async def validate_code(
        self, 
        code: str, 
        platform: str, 
        oauth_creds: Dict[str, str]
    ) -> Dict[str, Any]:
        """Comprehensive validation of generated MCP server code"""
        
        validation_results = {
            "passed": False,
            "syntax_valid": False,
            "imports_valid": False,
            "mcp_compliance": False,
            "oauth_implementation": False,
            "error_handling": False,
            "test_execution": False,
            "failures": [],
            "warnings": [],
            "error_details": ""
        }
        
        try:
            # Step 1: Syntax validation
            syntax_result = self._validate_syntax(code)
            validation_results["syntax_valid"] = syntax_result["valid"]
            if not syntax_result["valid"]:
                validation_results["failures"].append(f"Syntax error: {syntax_result['error']}")
                validation_results["error_details"] = syntax_result["error"]
                return validation_results
            
            # Step 2: Import validation
            import_result = self._validate_imports(code)
            validation_results["imports_valid"] = import_result["valid"]
            if not import_result["valid"]:
                validation_results["failures"].extend(import_result["errors"])
            
            # Step 3: MCP compliance check
            mcp_result = self._validate_mcp_compliance(code)
            validation_results["mcp_compliance"] = mcp_result["valid"]
            if not mcp_result["valid"]:
                validation_results["failures"].extend(mcp_result["errors"])
            
            # Step 4: OAuth implementation check
            oauth_result = self._validate_oauth_implementation(code, oauth_creds)
            validation_results["oauth_implementation"] = oauth_result["valid"]
            if not oauth_result["valid"]:
                validation_results["failures"].extend(oauth_result["errors"])
            
            # Step 5: Error handling validation
            error_handling_result = self._validate_error_handling(code)
            validation_results["error_handling"] = error_handling_result["valid"]
            if not error_handling_result["valid"]:
                validation_results["warnings"].extend(error_handling_result["warnings"])
            
            # Step 6: Runtime test execution
            if validation_results["syntax_valid"] and validation_results["mcp_compliance"]:
                test_result = await self._execute_runtime_tests(code, platform)
                validation_results["test_execution"] = test_result["passed"]
                if not test_result["passed"]:
                    validation_results["failures"].extend(test_result["failures"])
            
            # Overall pass determination
            validation_results["passed"] = (
                validation_results["syntax_valid"] and
                validation_results["imports_valid"] and 
                validation_results["mcp_compliance"] and
                validation_results["oauth_implementation"] and
                validation_results["test_execution"]
            )
            
        except Exception as e:
            validation_results["error_details"] = str(e)
            validation_results["failures"].append(f"Validation exception: {str(e)}")
        
        return validation_results
    
    def _validate_syntax(self, code: str) -> Dict[str, Any]:
        """Validate Python syntax"""
        
        try:
            ast.parse(code)
            return {"valid": True}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"Line {e.lineno}: {e.msg}"
            }
    
    def _validate_imports(self, code: str) -> Dict[str, Any]:
        """Validate that all imports are available and correct"""
        
        errors = []
        
        # Required MCP imports
        required_imports = [
            "from mcp import types",
            "from mcp.server import Server", 
            "from mcp.server.stdio import stdio_server"
        ]
        
        for required_import in required_imports:
            if required_import not in code:
                errors.append(f"Missing required import: {required_import}")
        
        # Check for potentially problematic imports
        problematic_patterns = [
            ("import subprocess", "subprocess import detected - potential security risk"),
            ("import os", "Direct os import detected - ensure proper usage"),
            ("from os import", "Direct os function import - verify security")
        ]
        
        for pattern, warning in problematic_patterns:
            if pattern in code:
                errors.append(f"Warning: {warning}")
        
        return {
            "valid": len([e for e in errors if not e.startswith("Warning:")]) == 0,
            "errors": errors
        }
    
    def _validate_mcp_compliance(self, code: str) -> Dict[str, Any]:
        """Validate MCP protocol compliance"""
        
        errors = []
        
        # Required MCP components
        required_components = [
            ("server = Server(", "Server instance creation"),
            ("@server.list_tools()", "list_tools decorator"),
            ("async def list_tools(", "list_tools function"),
            ("@server.call_tool()", "call_tool decorator"),
            ("async def call_tool(", "call_tool function"),
            ("types.Tool(", "Tool definition"),
            ("types.TextContent(", "TextContent response"),
            ("async def main(", "main function"),
            ("stdio_server()", "stdio_server usage")
        ]
        
        for pattern, description in required_components:
            if pattern not in code:
                errors.append(f"Missing {description}: {pattern}")
        
        # Check tool schema compliance
        if "inputSchema" not in code:
            errors.append("Tools must have inputSchema defined")
        
        if '"type": "object"' not in code:
            errors.append("Tool schemas must specify type as object")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _validate_oauth_implementation(self, code: str, oauth_creds: Dict[str, str]) -> Dict[str, Any]:
        """Validate OAuth implementation"""
        
        errors = []
        
        # Required OAuth components
        oauth_requirements = [
            ("CLIENT_ID", "OAuth Client ID definition"),
            ("CLIENT_SECRET", "OAuth Client Secret definition"),
            ("REDIRECT_URI", "OAuth Redirect URI definition"),
            ("get_auth_url", "OAuth URL generation method"),
            ("access_token", "Access token handling"),
        ]
        
        for pattern, description in oauth_requirements:
            if pattern not in code:
                errors.append(f"Missing {description}: {pattern}")
        
        # Check for proper environment variable usage
        if 'os.getenv' not in code and any(cred in code for cred in ['CLIENT_SECRET', 'CLIENT_ID']):
            errors.append("OAuth credentials should use environment variables")
        
        # Check for authentication tool
        if '"authenticate"' not in code:
            errors.append("Must include authenticate tool")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _validate_error_handling(self, code: str) -> Dict[str, Any]:
        """Validate error handling implementation"""
        
        warnings = []
        
        # Check for try/except blocks
        if 'try:' not in code or 'except' not in code:
            warnings.append("No error handling detected - consider adding try/except blocks")
        
        # Check for async function error handling
        async_functions = [line.strip() for line in code.split('\n') if 'async def' in line]
        if async_functions and 'try:' not in code:
            warnings.append("Async functions should include error handling")
        
        # Check for HTTP error handling
        if 'httpx' in code and 'raise_for_status' not in code:
            warnings.append("HTTP requests should check for errors with raise_for_status()")
        
        return {
            "valid": len(warnings) == 0,
            "warnings": warnings
        }
    
    async def _execute_runtime_tests(self, code: str, platform: str) -> Dict[str, Any]:
        """Execute runtime tests on the generated code"""
        
        try:
            # Create temporary file with the generated code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Create test file
            test_code = self._generate_test_code(platform)
            with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
                f.write(test_code)
                test_file = f.name
            
            # Run basic syntax check
            syntax_check = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'py_compile', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await syntax_check.communicate()
            
            if syntax_check.returncode != 0:
                return {
                    "passed": False,
                    "failures": [f"Syntax compilation failed: {stderr.decode()}"]
                }
            
            # Run import test
            import_test = await asyncio.create_subprocess_exec(
                sys.executable, '-c', f'import importlib.util; spec = importlib.util.spec_from_file_location("test_module", "{temp_file}"); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await import_test.communicate()
            
            if import_test.returncode != 0:
                return {
                    "passed": False, 
                    "failures": [f"Import test failed: {stderr.decode()}"]
                }
            
            # Basic functionality test
            functionality_test = await self._test_basic_functionality(temp_file)
            
            # Cleanup
            os.unlink(temp_file)
            os.unlink(test_file)
            
            return functionality_test
            
        except Exception as e:
            return {
                "passed": False,
                "failures": [f"Runtime test exception: {str(e)}"]
            }
    
    async def _test_basic_functionality(self, code_file: str) -> Dict[str, Any]:
        """Test basic MCP server functionality"""
        
        try:
            # Import the generated module
            spec = importlib.util.spec_from_file_location("generated_server", code_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Test that server exists
            if not hasattr(module, 'server'):
                return {
                    "passed": False,
                    "failures": ["No server instance found"]
                }
            
            server = module.server
            
            # Test list_tools
            try:
                tools = await server.list_tools()
                if not tools:
                    return {
                        "passed": False,
                        "failures": ["No tools returned from list_tools()"]
                    }
                
                # Check that authenticate tool exists
                tool_names = [tool.name for tool in tools]
                if 'authenticate' not in tool_names:
                    return {
                        "passed": False,
                        "failures": ["Missing required 'authenticate' tool"]
                    }
                
            except Exception as e:
                return {
                    "passed": False,
                    "failures": [f"list_tools() failed: {str(e)}"]
                }
            
            # Test call_tool with authenticate
            try:
                result = await server.call_tool('authenticate', {})
                if not result or not isinstance(result, list):
                    return {
                        "passed": False,
                        "failures": ["authenticate tool returned invalid response"]
                    }
                
            except Exception as e:
                return {
                    "passed": False,
                    "failures": [f"call_tool('authenticate') failed: {str(e)}"]
                }
            
            return {"passed": True, "failures": []}
            
        except Exception as e:
            return {
                "passed": False,
                "failures": [f"Basic functionality test failed: {str(e)}"]
            }
    
    def _generate_test_code(self, platform: str) -> str:
        """Generate platform-specific test code"""
        
        return f'''#!/usr/bin/env python3
"""
Generated test code for {platform} MCP server validation
"""

import asyncio
import pytest

async def test_server_basic_functionality():
    """Test basic server functionality"""
    # This would contain platform-specific tests
    pass

if __name__ == "__main__":
    asyncio.run(test_server_basic_functionality())
'''
