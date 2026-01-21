#!/usr/bin/env python3
"""
Pipeline Orchestrator - Connects all MCP Builder components
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

# Import components
from llm.code_generator import CodeGenerator
from host.deployer import Deployer
from host.config import DeploymentConfig


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPBuilderPipeline:
    """Orchestrates the complete MCP server build and deployment pipeline"""
    
    def __init__(self):
        self.code_generator = CodeGenerator()
        self.deployment_config = DeploymentConfig()
        self.deployer = Deployer(self.deployment_config)
        self.builds_base_path = Path(__file__).parent / "builds"
        
    async def execute_build_pipeline(
        self,
        user_uuid: str,
        user_email: str,
        platform: str,
        description: str,
        oauth_creds: Dict[str, str],
        version: int
    ) -> Dict[str, Any]:
        """Execute the complete build pipeline from request to deployment"""
        
        pipeline_result = {
            "success": False,
            "build_id": f"{user_uuid}/{platform}/v{version}",
            "stages": {},
            "error": None,
            "deployment_info": None
        }
        
        build_path = self.builds_base_path / user_uuid / platform / str(version)
        
        try:
            logger.info(f"Starting pipeline for {pipeline_result['build_id']}")
            
            # Stage 1: Setup build directory
            logger.info("Stage 1: Setting up build directory")
            setup_result = await self._setup_build_directory(
                build_path, platform, description, oauth_creds, user_uuid, version
            )
            pipeline_result["stages"]["setup"] = setup_result
            
            if not setup_result["success"]:
                pipeline_result["error"] = setup_result["error"]
                return pipeline_result
            
            # Stage 2: Generate MCP server code
            logger.info("Stage 2: Generating MCP server code")
            generation_result = await self._generate_code_stage(
                platform, description, oauth_creds, user_uuid, version, build_path
            )
            pipeline_result["stages"]["code_generation"] = generation_result
            
            if not generation_result["success"]:
                pipeline_result["error"] = generation_result["error"]
                return pipeline_result
            
            # Stage 3: Save generated code
            logger.info("Stage 3: Saving generated code")
            save_result = await self._save_generated_code(
                build_path, generation_result["code"]
            )
            pipeline_result["stages"]["save_code"] = save_result
            
            if not save_result["success"]:
                pipeline_result["error"] = save_result["error"]
                return pipeline_result
            
            # Stage 4: Deploy to hosting platform
            logger.info("Stage 4: Deploying to hosting platform")
            deployment_result = await self._deploy_stage(
                user_uuid, platform, version, build_path
            )
            pipeline_result["stages"]["deployment"] = deployment_result
            pipeline_result["deployment_info"] = deployment_result.get("deployment_info")
            
            if not deployment_result["success"]:
                pipeline_result["error"] = deployment_result["error"]
                return pipeline_result
            
            # Stage 5: Send notification
            logger.info("Stage 5: Sending deployment notification")
            notification_result = await self._notification_stage(
                user_email, platform, deployment_result["deployment_info"]
            )
            pipeline_result["stages"]["notification"] = notification_result
            
            # Pipeline completed successfully
            pipeline_result["success"] = True
            logger.info(f"Pipeline completed successfully for {pipeline_result['build_id']}")
            
            return pipeline_result
            
        except Exception as e:
            logger.error(f"Pipeline failed for {pipeline_result['build_id']}: {str(e)}")
            pipeline_result["error"] = str(e)
            return pipeline_result
    
    async def _setup_build_directory(
        self,
        build_path: Path,
        platform: str,
        description: str,
        oauth_creds: Dict[str, str],
        user_uuid: str,
        version: int
    ) -> Dict[str, Any]:
        """Setup build directory structure and metadata"""
        
        try:
            # Create directory structure
            build_path.mkdir(parents=True, exist_ok=True)
            (build_path / "mcp").mkdir(exist_ok=True)
            
            # Create prompt.txt with build request
            prompt_data = {
                "platform": platform,
                "description": description,
                "oauth_credentials": {
                    "client_id": oauth_creds["client_id"],
                    "client_secret": oauth_creds["client_secret"], 
                    "redirect_url": oauth_creds["redirect_url"]
                },
                "user_uuid": user_uuid,
                "version": version,
                "timestamp": datetime.now().isoformat(),
                "status": "building"
            }
            
            with open(build_path / "prompt.txt", "w") as f:
                f.write(json.dumps(prompt_data, indent=2))
            
            # Create metadata.json
            metadata = {
                "build_id": f"{user_uuid}/{platform}/v{version}",
                "created_at": datetime.now().isoformat(),
                "platform": platform,
                "version": version,
                "user_uuid": user_uuid,
                "status": "building",
                "stages": []
            }
            
            with open(build_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            return {"success": True}
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Build directory setup failed: {str(e)}"
            }
    
    async def _generate_code_stage(
        self,
        platform: str,
        description: str,
        oauth_creds: Dict[str, str],
        user_uuid: str,
        version: int,
        build_path: Path
    ) -> Dict[str, Any]:
        """Execute code generation stage"""
        
        try:
            # Load previous versions for context
            previous_versions = await self._load_previous_versions(
                user_uuid, platform, version
            )
            
            # Generate MCP server code
            generation_result = await self.code_generator.generate_mcp_server(
                platform=platform,
                description=description,
                oauth_creds=oauth_creds,
                user_uuid=user_uuid,
                version=version,
                previous_versions=previous_versions
            )
            
            if not generation_result["success"]:
                return {
                    "success": False,
                    "error": f"Code generation failed: {generation_result.get('error', 'Unknown error')}"
                }
            
            # Update metadata with generation results
            await self._update_build_metadata(build_path, {
                "code_generation": {
                    "completed_at": datetime.now().isoformat(),
                    "attempt": generation_result.get("attempt", 1),
                    "test_results": generation_result.get("test_results", {})
                }
            })
            
            return {
                "success": True,
                "code": generation_result["code"],
                "test_results": generation_result.get("test_results", {}),
                "attempt": generation_result.get("attempt", 1)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Code generation stage failed: {str(e)}"
            }
    
    async def _save_generated_code(self, build_path: Path, generated_code: str) -> Dict[str, Any]:
        """Save generated code to build directory"""
        
        try:
            mcp_dir = build_path / "mcp"
            
            # Save main server file
            server_file = mcp_dir / "server.py"
            with open(server_file, "w") as f:
                f.write(generated_code)
            
            # Copy requirements.txt from template
            template_requirements = Path(__file__).parent / "cookiecutter" / "requirements.txt"
            if template_requirements.exists():
                import shutil
                shutil.copy2(template_requirements, mcp_dir / "requirements.txt")
            
            # Generate test file from template
            test_template = Path(__file__).parent / "cookiecutter" / "test_{{cookiecutter.platform_name}}_server.py"
            if test_template.exists():
                with open(test_template, "r") as f:
                    test_content = f.read()
                
                # Replace template variables
                test_content = test_content.replace("{{cookiecutter.platform_name}}", "generated")
                
                with open(mcp_dir / "test_server.py", "w") as f:
                    f.write(test_content)
            
            # Create README for the generated server
            readme_content = f"""# Generated MCP Server

This MCP server was automatically generated by the MCP Builder system.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python server.py
```

## Testing

```bash
python test_server.py
```

Generated at: {datetime.now().isoformat()}
"""
            
            with open(mcp_dir / "README.md", "w") as f:
                f.write(readme_content)
            
            return {"success": True}
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Code save failed: {str(e)}"
            }
    
    async def _deploy_stage(
        self,
        user_uuid: str,
        platform: str,
        version: int,
        build_path: Path
    ) -> Dict[str, Any]:
        """Execute deployment stage"""
        
        try:
            deployment_result = await self.deployer.deploy_mcp_server(
                user_uuid, platform, version, build_path
            )
            
            # Update build metadata with deployment info
            if deployment_result["success"]:
                await self._update_build_metadata(build_path, {
                    "deployment": {
                        "completed_at": datetime.now().isoformat(),
                        "github_repo": deployment_result["github_repo"],
                        "fastmcp_url": deployment_result["fastmcp_url"],
                        "deployment_url": deployment_result["deployment_url"]
                    },
                    "status": "deployed"
                })
            else:
                await self._update_build_metadata(build_path, {
                    "status": "deployment_failed",
                    "deployment_error": deployment_result["error"]
                })
            
            return {
                "success": deployment_result["success"],
                "error": deployment_result.get("error"),
                "deployment_info": deployment_result if deployment_result["success"] else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Deployment stage failed: {str(e)}"
            }
    
    async def _notification_stage(
        self,
        user_email: str,
        platform: str,
        deployment_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute notification stage"""
        
        try:
            await self.deployer.send_deployment_notification(
                user_email, platform, deployment_info or {}
            )
            
            return {"success": True}
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Notification failed: {str(e)}"
            }
    
    async def _load_previous_versions(
        self,
        user_uuid: str,
        platform: str,
        current_version: int
    ) -> list[Dict[str, Any]]:
        """Load previous versions for context"""
        
        previous_versions = []
        base_path = self.builds_base_path / user_uuid / platform
        
        if not base_path.exists():
            return previous_versions
        
        for version_num in range(1, current_version):
            version_path = base_path / str(version_num)
            if version_path.exists():
                metadata_file = version_path / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)
                        previous_versions.append(metadata)
        
        return previous_versions
    
    async def _update_build_metadata(self, build_path: Path, updates: Dict[str, Any]) -> None:
        """Update build metadata with new information"""
        
        metadata_file = build_path / "metadata.json"
        
        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
        else:
            metadata = {}
        
        metadata.update(updates)
        metadata["last_updated"] = datetime.now().isoformat()
        
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)


# Global pipeline instance
pipeline = MCPBuilderPipeline()
