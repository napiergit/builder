#!/usr/bin/env python3
"""
Guardrails Engine - Safety and quality constraints for generated code
"""

import ast
import re
import json
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass


@dataclass
class GuardrailViolation:
    """Represents a guardrail violation"""
    rule: str
    severity: str  # "error", "warning", "info"
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


class GuardrailsEngine:
    """Enforces safety and quality guardrails on generated code"""
    
    def __init__(self):
        self.forbidden_imports = {
            'subprocess', 'os.system', 'eval', 'exec', 'compile',
            '__import__', 'open', 'file', 'input', 'raw_input'
        }
        
        self.forbidden_functions = {
            'eval', 'exec', 'compile', 'globals', 'locals', 
            'setattr', 'delattr', 'hasattr', '__import__'
        }
        
        self.required_patterns = [
            r'from mcp import types',
            r'from mcp\.server import Server',
            r'async def list_tools\(\)',
            r'async def call_tool\(\)'
        ]
        
        self.security_patterns = [
            (r'CLIENT_SECRET\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret detected'),
            (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password detected'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key detected'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'Hardcoded token detected')
        ]
    
    def validate_and_sanitize(self, code: str) -> str:
        """Validate code against guardrails and return sanitized version"""
        
        violations = self.check_violations(code)
        
        # Handle critical violations
        critical_violations = [v for v in violations if v.severity == "error"]
        if critical_violations:
            raise GuardrailException(f"Critical violations found: {[v.message for v in critical_violations]}")
        
        # Apply automatic fixes for warnings
        sanitized_code = self._apply_automatic_fixes(code, violations)
        
        return sanitized_code
    
    def check_violations(self, code: str) -> List[GuardrailViolation]:
        """Check code for guardrail violations"""
        
        violations = []
        
        # Parse AST for deep analysis
        try:
            tree = ast.parse(code)
            violations.extend(self._check_ast_violations(tree))
        except SyntaxError as e:
            violations.append(GuardrailViolation(
                rule="syntax",
                severity="error",
                message=f"Syntax error: {str(e)}",
                line_number=e.lineno
            ))
            return violations
        
        # Check security patterns
        violations.extend(self._check_security_patterns(code))
        
        # Check required MCP patterns
        violations.extend(self._check_required_patterns(code))
        
        # Check code quality
        violations.extend(self._check_code_quality(code))
        
        return violations
    
    def _check_ast_violations(self, tree: ast.AST) -> List[GuardrailViolation]:
        """Check AST for security and safety violations"""
        
        violations = []
        
        for node in ast.walk(tree):
            # Check for forbidden imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.forbidden_imports:
                        violations.append(GuardrailViolation(
                            rule="forbidden_import",
                            severity="error", 
                            message=f"Forbidden import: {alias.name}",
                            line_number=node.lineno,
                            suggestion=f"Remove import {alias.name} or use safer alternative"
                        ))
            
            elif isinstance(node, ast.ImportFrom):
                if node.module in self.forbidden_imports:
                    violations.append(GuardrailViolation(
                        rule="forbidden_import",
                        severity="error",
                        message=f"Forbidden import from: {node.module}",
                        line_number=node.lineno
                    ))
            
            # Check for forbidden function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.forbidden_functions:
                        violations.append(GuardrailViolation(
                            rule="forbidden_function",
                            severity="error",
                            message=f"Forbidden function call: {node.func.id}",
                            line_number=node.lineno
                        ))
                
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in self.forbidden_functions:
                        violations.append(GuardrailViolation(
                            rule="forbidden_function",
                            severity="warning",
                            message=f"Potentially unsafe function call: {node.func.attr}",
                            line_number=node.lineno
                        ))
            
            # Check for hardcoded secrets in string literals
            elif isinstance(node, ast.Str):
                if self._looks_like_secret(node.s):
                    violations.append(GuardrailViolation(
                        rule="hardcoded_secret",
                        severity="warning",
                        message="Potential hardcoded secret in string literal",
                        line_number=node.lineno,
                        suggestion="Use environment variables or config files"
                    ))
        
        return violations
    
    def _check_security_patterns(self, code: str) -> List[GuardrailViolation]:
        """Check for security anti-patterns using regex"""
        
        violations = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern, message in self.security_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(GuardrailViolation(
                        rule="security_pattern",
                        severity="error",
                        message=message,
                        line_number=i,
                        suggestion="Use environment variables instead"
                    ))
        
        return violations
    
    def _check_required_patterns(self, code: str) -> List[GuardrailViolation]:
        """Check that required MCP patterns are present"""
        
        violations = []
        
        for pattern in self.required_patterns:
            if not re.search(pattern, code):
                violations.append(GuardrailViolation(
                    rule="missing_required_pattern",
                    severity="error", 
                    message=f"Missing required MCP pattern: {pattern}",
                    suggestion="Ensure all required MCP server components are implemented"
                ))
        
        return violations
    
    def _check_code_quality(self, code: str) -> List[GuardrailViolation]:
        """Check code quality metrics"""
        
        violations = []
        lines = code.split('\n')
        
        # Check for excessive line length
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                violations.append(GuardrailViolation(
                    rule="line_length",
                    severity="warning",
                    message="Line exceeds 120 characters",
                    line_number=i,
                    suggestion="Break long lines for better readability"
                ))
        
        # Check for missing error handling in async functions
        if 'async def' in code and 'try:' not in code:
            violations.append(GuardrailViolation(
                rule="error_handling",
                severity="warning",
                message="Async functions should include error handling",
                suggestion="Add try/except blocks for robust error handling"
            ))
        
        # Check for OAuth credentials handling
        if 'CLIENT_SECRET' in code and 'os.getenv' not in code:
            violations.append(GuardrailViolation(
                rule="credential_handling",
                severity="warning",
                message="OAuth credentials should be loaded from environment",
                suggestion="Use os.getenv() to load sensitive credentials"
            ))
        
        return violations
    
    def _looks_like_secret(self, text: str) -> bool:
        """Heuristic to detect potential secrets"""
        
        # Skip very short strings
        if len(text) < 10:
            return False
        
        # Look for patterns that suggest secrets
        secret_indicators = [
            r'^[A-Za-z0-9+/]{20,}={0,2}$',  # Base64-like
            r'^[a-f0-9]{32,}$',              # Hex strings
            r'^sk_[a-z0-9]{20,}$',           # API key pattern
            r'^[A-Z0-9]{20,}$'               # All caps alphanumeric
        ]
        
        for pattern in secret_indicators:
            if re.match(pattern, text):
                return True
        
        return False
    
    def _apply_automatic_fixes(self, code: str, violations: List[GuardrailViolation]) -> str:
        """Apply automatic fixes for common violations"""
        
        fixed_code = code
        
        for violation in violations:
            if violation.severity == "warning":
                if violation.rule == "hardcoded_secret":
                    # Replace hardcoded secrets with environment variable references
                    fixed_code = self._fix_hardcoded_secrets(fixed_code)
                
                elif violation.rule == "credential_handling":
                    # Add environment variable loading for credentials
                    fixed_code = self._fix_credential_handling(fixed_code)
        
        return fixed_code
    
    def _fix_hardcoded_secrets(self, code: str) -> str:
        """Replace hardcoded secrets with environment variables"""
        
        # Replace common secret patterns
        replacements = [
            (r'CLIENT_SECRET\s*=\s*["\'][^"\']+["\']', 'CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")'),
            (r'CLIENT_ID\s*=\s*["\'][^"\']+["\']', 'CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'api_key = os.getenv("API_KEY")'),
        ]
        
        fixed_code = code
        for pattern, replacement in replacements:
            fixed_code = re.sub(pattern, replacement, fixed_code)
        
        # Ensure os import is present
        if 'import os' not in fixed_code and 'os.getenv' in fixed_code:
            fixed_code = 'import os\n' + fixed_code
        
        return fixed_code
    
    def _fix_credential_handling(self, code: str) -> str:
        """Fix credential handling to use environment variables"""
        
        if 'import os' not in code:
            code = 'import os\n' + code
        
        return code


class GuardrailException(Exception):
    """Exception raised when critical guardrail violations are found"""
    pass
