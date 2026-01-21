#!/usr/bin/env python3
"""
Deployer - Handles deployment of generated MCP servers to hosting platforms
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import httpx
import subprocess
from datetime import datetime

from .config import DeploymentConfig


class Deployer:
    """Manages deployment of MCP servers to various hosting platforms"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.fastmcp_api_key = os.getenv("FASTMCP_API_KEY")
    
    async def deploy_mcp_server(
        self, 
        user_uuid: str, 
        platform: str, 
        version: int,
        build_path: Path
    ) -> Dict[str, Any]:
        """Deploy MCP server through complete pipeline"""
        
        deployment_result = {
            "success": False,
            "github_repo": None,
            "fastmcp_url": None,
            "deployment_url": None,
            "error": None
        }
        
        try:
            # Step 1: Create GitHub repository
            repo_info = await self._create_github_repo(user_uuid, platform, version, build_path)
            if not repo_info["success"]:
                deployment_result["error"] = repo_info["error"]
                return deployment_result
            
            deployment_result["github_repo"] = repo_info["repo_url"]
            
            # Step 2: Push code to repository
            push_result = await self._push_code_to_repo(build_path, repo_info["clone_url"])
            if not push_result["success"]:
                deployment_result["error"] = push_result["error"]
                return deployment_result
            
            # Step 3: Link to FastMCP.cloud
            fastmcp_result = await self._link_to_fastmcp(repo_info["repo_name"], user_uuid)
            if not fastmcp_result["success"]:
                deployment_result["error"] = fastmcp_result["error"] 
                return deployment_result
            
            deployment_result["fastmcp_url"] = fastmcp_result["fastmcp_url"]
            deployment_result["deployment_url"] = fastmcp_result["deployment_url"]
            
            # Step 4: Verify deployment health
            health_check = await self._verify_deployment_health(fastmcp_result["deployment_url"])
            if not health_check["healthy"]:
                deployment_result["error"] = f"Deployment failed health check: {health_check['error']}"
                return deployment_result
            
            # Step 5: Save deployment metadata
            await self._save_deployment_metadata(build_path, deployment_result)
            
            deployment_result["success"] = True
            return deployment_result
            
        except Exception as e:
            deployment_result["error"] = str(e)
            return deployment_result
    
    async def _create_github_repo(
        self, 
        user_uuid: str, 
        platform: str, 
        version: int, 
        build_path: Path
    ) -> Dict[str, Any]:
        """Create GitHub repository using Terraform"""
        
        try:
            repo_name = f"mcp-{platform}-{user_uuid[:8]}"
            
            # Use Terraform to create repository
            terraform_vars = {
                "repo_name": repo_name,
                "description": f"Generated MCP server for {platform}",
                "private": False,  # Public for fastmcp.cloud integration
                "auto_init": True
            }
            
            # Apply Terraform configuration
            terraform_result = await self._apply_terraform(terraform_vars)
            if not terraform_result["success"]:
                return terraform_result
            
            return {
                "success": True,
                "repo_name": repo_name,
                "repo_url": f"https://github.com/{self.config.github_org}/{repo_name}",
                "clone_url": f"https://github.com/{self.config.github_org}/{repo_name}.git"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"GitHub repo creation failed: {str(e)}"
            }
    
    async def _apply_terraform(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Terraform configuration for repository creation"""
        
        try:
            terraform_dir = Path(__file__).parent / "terraform"
            
            # Write variables to tfvars file
            tfvars_content = "\n".join([f'{k} = "{v}"' for k, v in variables.items()])
            with open(terraform_dir / "terraform.tfvars", "w") as f:
                f.write(tfvars_content)
            
            # Run terraform commands
            commands = [
                ["terraform", "init"],
                ["terraform", "plan"],
                ["terraform", "apply", "-auto-approve"]
            ]
            
            for cmd in commands:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=terraform_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Terraform {cmd[1]} failed: {stderr.decode()}"
                    }
            
            return {"success": True}
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Terraform execution failed: {str(e)}"
            }
    
    async def _push_code_to_repo(self, build_path: Path, clone_url: str) -> Dict[str, Any]:
        """Push generated code to GitHub repository"""
        
        try:
            # Clone repository
            temp_repo_path = build_path.parent / "temp_repo"
            
            clone_cmd = ["git", "clone", clone_url, str(temp_repo_path)]
            process = await asyncio.create_subprocess_exec(
                *clone_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "error": f"Git clone failed: {stderr.decode()}"
                }
            
            # Copy MCP code to repository
            mcp_source = build_path / "mcp"
            if mcp_source.exists():
                import shutil
                for item in mcp_source.iterdir():
                    if item.is_file():
                        shutil.copy2(item, temp_repo_path)
                    else:
                        shutil.copytree(item, temp_repo_path / item.name, dirs_exist_ok=True)
            
            # Add, commit, and push
            git_commands = [
                ["git", "add", "."],
                ["git", "commit", "-m", "Initial MCP server deployment"],
                ["git", "push", "origin", "main"]
            ]
            
            for cmd in git_commands:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=temp_repo_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0 and "nothing to commit" not in stderr.decode():
                    return {
                        "success": False,
                        "error": f"Git {cmd[1]} failed: {stderr.decode()}"
                    }
            
            # Cleanup temp directory
            import shutil
            shutil.rmtree(temp_repo_path)
            
            return {"success": True}
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Code push failed: {str(e)}"
            }
    
    async def _link_to_fastmcp(self, repo_name: str, user_uuid: str) -> Dict[str, Any]:
        """Deploy generated MCP server to FastMCP.cloud using GitHub integration"""
        
        try:
            # Create fastmcp.json config in the generated MCP server repo
            build_path = Path(__file__).parent.parent / "builds" / user_uuid / repo_name.split('-')[0] / "1"
            
            # Generate fastmcp.cloud deployment config
            fastmcp_config = {
                "name": repo_name,
                "description": f"Generated MCP server for {repo_name.split('-')[0]} platform",
                "version": "1.0.0",
                "main": "server.py",
                "runtime": "python3.9",
                "dependencies": {
                    "python": "requirements.txt"
                }
            }
            
            # Write fastmcp.json to build directory
            config_file = build_path / "fastmcp.json"
            with open(config_file, "w") as f:
                json.dump(fastmcp_config, f, indent=2)
            
            # Create GitHub Actions workflow for the generated server
            workflow_dir = build_path / ".github" / "workflows"
            workflow_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_content = f"""name: Deploy to FastMCP Cloud

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.9'
    
    - name: Deploy to FastMCP Cloud
      env:
        FASTMCP_API_KEY: ${{{{ secrets.FASTMCP_API_KEY }}}}
      run: |
        curl -X POST "https://fastmcp.cloud/api/github/deploy" \\
          -H "Authorization: Bearer $FASTMCP_API_KEY" \\
          -H "Content-Type: application/json" \\
          -d '{{
            "repository": "${{{{ github.repository }}}}",
            "ref": "${{{{ github.ref }}}}",
            "sha": "${{{{ github.sha }}}}"
          }}'
"""
            
            workflow_file = workflow_dir / "deploy.yml"
            with open(workflow_file, "w") as f:
                f.write(workflow_content)
            
            return {
                "success": True,
                "fastmcp_url": f"https://fastmcp.cloud/{self.config.github_org}/{repo_name}",
                "deployment_url": f"https://{repo_name}.fastmcp.cloud",
                "config_created": True,
                "next_steps": [
                    "GitHub repository will be created with fastmcp.json",
                    "GitHub Actions will auto-deploy to fastmcp.cloud",
                    f"Set FASTMCP_API_KEY secret in {self.config.github_org}/{repo_name}"
                ]
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"FastMCP linking failed: {str(e)}"
            }
    
    async def _verify_deployment_health(self, deployment_url: str) -> Dict[str, Any]:
        """Verify that deployed MCP server is healthy"""
        
        try:
            # Wait for deployment to be ready
            await asyncio.sleep(30)
            
            async with httpx.AsyncClient() as client:
                # Check health endpoint
                health_response = await client.get(
                    f"{deployment_url}/health",
                    timeout=10
                )
                
                if health_response.status_code == 200:
                    return {"healthy": True}
                else:
                    return {
                        "healthy": False,
                        "error": f"Health check failed with status {health_response.status_code}"
                    }
                    
        except Exception as e:
            return {
                "healthy": False,
                "error": f"Health check failed: {str(e)}"
            }
    
    async def _save_deployment_metadata(self, build_path: Path, deployment_result: Dict[str, Any]) -> None:
        """Save deployment metadata to build directory"""
        
        deployment_metadata = {
            "deployed_at": datetime.now().isoformat(),
            "github_repo": deployment_result.get("github_repo"),
            "fastmcp_url": deployment_result.get("fastmcp_url"),
            "deployment_url": deployment_result.get("deployment_url"),
            "deployment_method": "fastmcp_cloud",
            "terraform_managed": True
        }
        
        metadata_file = build_path / "deployment.json"
        with open(metadata_file, "w") as f:
            json.dump(deployment_metadata, f, indent=2)
    
    async def send_deployment_notification(
        self, 
        user_email: str, 
        platform: str, 
        deployment_result: Dict[str, Any]
    ) -> None:
        """Print deployment status for generated MCP server"""
        
        if deployment_result.get("success"):
            message = f"""
✅ MCP SERVER DEPLOYMENT SETUP COMPLETE

Your {platform} MCP server has been prepared for deployment!

📦 GitHub Repository: {deployment_result.get('github_repo', 'Repository created')}
🚀 FastMCP URL: {deployment_result.get('fastmcp_url', 'Pending deployment')}
🔗 Live URL: {deployment_result.get('deployment_url', 'Will be available after deployment')}

NEXT STEPS:
{chr(10).join('  - ' + step for step in deployment_result.get('next_steps', ['GitHub Actions will handle deployment']))}

The generated MCP server will automatically deploy to fastmcp.cloud via GitHub Actions.
            """
        else:
            message = f"""
❌ MCP SERVER DEPLOYMENT FAILED

Platform: {platform}
Error: {deployment_result.get('error', 'Unknown error')}

Please check the build logs and try again.
            """
        
        print(f"📧 NOTIFICATION for {user_email}:")
        print(message)
