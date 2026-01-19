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

from config import DeploymentConfig


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
        """Link GitHub repository to FastMCP.cloud for deployment"""
        
        try:
            async with httpx.AsyncClient() as client:
                # FastMCP.cloud API call to link repository
                link_request = {
                    "repository": f"{self.config.github_org}/{repo_name}",
                    "user_id": user_uuid,
                    "auto_deploy": True,
                    "environment": "production"
                }
                
                response = await client.post(
                    f"{self.config.fastmcp_api_url}/link-repository",
                    json=link_request,
                    headers={
                        "Authorization": f"Bearer {self.fastmcp_api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"FastMCP linking failed: {response.text}"
                    }
                
                link_result = response.json()
                
                return {
                    "success": True,
                    "fastmcp_url": link_result.get("project_url"),
                    "deployment_url": link_result.get("deployment_url")
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
        """Send email notification about deployment completion"""
        
        if deployment_result["success"]:
            subject = f"MCP Server Deployed: {platform}"
            message = f"""
Your MCP server for {platform} has been successfully deployed!

Access your server at: {deployment_result['deployment_url']}
GitHub Repository: {deployment_result['github_repo']}
FastMCP Project: {deployment_result['fastmcp_url']}

To add this server to your MCP client, use the deployment URL above.
            """
        else:
            subject = f"MCP Server Deployment Failed: {platform}"
            message = f"""
Your MCP server deployment for {platform} failed.

Error: {deployment_result['error']}

Please contact support if this issue persists.
            """
        
        # In real implementation, this would send actual email
        # For now, just log the notification
        print(f"Email notification to {user_email}: {subject}")
        print(message)
