#!/usr/bin/env python3
"""
Deployment Configuration Management
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DeploymentConfig:
    """Configuration for deployment infrastructure"""
    
    # GitHub Configuration
    github_org: str = "mcp-builder-org"
    github_token: Optional[str] = None
    
    # FastMCP Configuration  
    fastmcp_api_url: str = "https://api.fastmcp.cloud"
    fastmcp_api_key: Optional[str] = None
    
    # Deployment Settings
    auto_deploy: bool = True
    deployment_timeout: int = 300  # seconds
    health_check_retries: int = 3
    health_check_interval: int = 30  # seconds
    
    # Repository Settings
    default_repo_visibility: str = "public"  # Required for fastmcp.cloud
    enable_branch_protection: bool = True
    enable_webhooks: bool = True
    
    def __post_init__(self):
        """Load configuration from environment variables"""
        self.github_token = self.github_token or os.getenv("GITHUB_TOKEN")
        self.fastmcp_api_key = self.fastmcp_api_key or os.getenv("FASTMCP_API_KEY")
        
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable required")
        
        if not self.fastmcp_api_key:
            raise ValueError("FASTMCP_API_KEY environment variable required")


# Global configuration instance
deployment_config = DeploymentConfig()
