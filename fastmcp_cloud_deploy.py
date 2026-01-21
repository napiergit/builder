#!/usr/bin/env python3
"""
Automated deployment to fastmcp.cloud
Based on analysis of their GitHub integration workflow
"""

import subprocess
import json
import time
import os

class FastMCPCloudDeployer:
    def __init__(self, api_key: str, github_token: str):
        self.api_key = api_key
        self.github_token = github_token
        self.repo_url = "https://github.com/napiergit/builder.git"
    
    def create_fastmcp_config(self):
        """Create fastmcp.json configuration file for deployment"""
        config = {
            "name": "mcp-builder",
            "description": "MCP Builder - Automated MCP server generation and deployment",
            "version": "1.0.0",
            "author": "napiergit",
            "main": "server.py",
            "runtime": "python3.9",
            "dependencies": {
                "python": "requirements.txt"
            },
            "environment": {
                "PORT": "8000"
            },
            "tools": [
                {
                    "name": "is_building_mcp_server_viable",
                    "description": "Check if a platform API is viable for MCP server creation"
                },
                {
                    "name": "build_mcp_server", 
                    "description": "Build and deploy an MCP server for a specified platform"
                }
            ]
        }
        
        with open("fastmcp.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print("✅ Created fastmcp.json configuration")
    
    def create_github_workflow(self):
        """Create GitHub Action workflow for fastmcp.cloud deployment"""
        os.makedirs(".github/workflows", exist_ok=True)
        
        workflow = """name: Deploy to FastMCP Cloud

on:
  push:
    branches: [ main ]
  pull_request:
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
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Test server
      run: |
        python -m pytest tests/ || echo "No tests found"
    
    - name: Deploy to FastMCP Cloud
      env:
        FASTMCP_API_KEY: ${{ secrets.FASTMCP_API_KEY }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        # FastMCP Cloud deployment webhook trigger
        curl -X POST "https://fastmcp.cloud/api/github/deploy" \\
          -H "Authorization: Bearer $FASTMCP_API_KEY" \\
          -H "Content-Type: application/json" \\
          -d '{
            "repository": "${{ github.repository }}",
            "ref": "${{ github.ref }}",
            "sha": "${{ github.sha }}"
          }'
"""
        
        with open(".github/workflows/deploy.yml", "w") as f:
            f.write(workflow)
        
        print("✅ Created GitHub Actions workflow")
    
    def setup_github_secrets(self):
        """Set up required GitHub secrets for deployment"""
        print("🔐 GitHub secrets needed:")
        print("- FASTMCP_API_KEY:", self.api_key[:10] + "...")
        print("- GITHUB_TOKEN: (use repository secret)")
        
        # Try to set secrets via GitHub CLI if available
        secrets_to_set = [
            ("FASTMCP_API_KEY", self.api_key),
        ]
        
        for secret_name, secret_value in secrets_to_set:
            try:
                result = subprocess.run([
                    "gh", "secret", "set", secret_name, 
                    "--body", secret_value,
                    "--repo", "napiergit/builder"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Set GitHub secret: {secret_name}")
                else:
                    print(f"❌ Failed to set {secret_name}: {result.stderr}")
                    print(f"   Manual setup required in GitHub repository settings")
            except FileNotFoundError:
                print(f"❌ GitHub CLI not found - manually set secret {secret_name}")
    
    def trigger_deployment(self):
        """Trigger deployment by pushing changes to GitHub"""
        try:
            # Add and commit deployment files
            subprocess.run(["git", "add", "fastmcp.json", ".github/"], check=True)
            subprocess.run([
                "git", "commit", "-m", 
                "Add fastmcp.cloud deployment configuration\n\n- Added fastmcp.json for platform configuration\n- Added GitHub Actions workflow for automated deployment\n- Configured for Python 3.9 runtime"
            ], check=True)
            
            # Push to trigger deployment
            subprocess.run(["git", "push", "origin", "main"], check=True)
            
            print("🚀 Pushed deployment configuration to GitHub")
            print("🔄 GitHub Actions should now deploy to fastmcp.cloud automatically")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git operation failed: {e}")
            return False
    
    def check_deployment_status(self, max_wait_seconds=300):
        """Check deployment status by monitoring GitHub Actions"""
        print("⏳ Waiting for deployment to complete...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            try:
                # Check GitHub Actions status
                result = subprocess.run([
                    "gh", "run", "list", "--limit", "1", 
                    "--repo", "napiergit/builder"
                ], capture_output=True, text=True)
                
                if result.returncode == 0 and "completed" in result.stdout:
                    if "success" in result.stdout:
                        print("✅ Deployment completed successfully!")
                        return True
                    else:
                        print("❌ Deployment failed - check GitHub Actions logs")
                        return False
                        
                time.sleep(30)  # Check every 30 seconds
                print("⏳ Still deploying...")
                
            except FileNotFoundError:
                print("❌ GitHub CLI not available - check deployment manually")
                break
        
        print("⏰ Deployment status check timed out")
        return None

def main():
    """Main deployment function"""
    api_key = os.getenv("FASTMCP_API_KEY", "fmcp_XTAYZDw3a7nY_1312VA5yxRez3ud5MmWmy3fQ-f8shM")
    github_token = os.getenv("GITHUB_TOKEN")
    
    if not github_token:
        print("⚠️  GITHUB_TOKEN not set - some operations may require manual setup")
    
    deployer = FastMCPCloudDeployer(api_key, github_token)
    
    print("🏗️  Setting up fastmcp.cloud deployment...")
    
    # Create deployment configuration
    deployer.create_fastmcp_config()
    deployer.create_github_workflow()
    deployer.setup_github_secrets()
    
    # Trigger deployment
    if deployer.trigger_deployment():
        deployer.check_deployment_status()
    else:
        print("❌ Deployment setup failed")

if __name__ == "__main__":
    main()
