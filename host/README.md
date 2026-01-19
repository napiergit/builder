# Host Infrastructure

Deployment and hosting infrastructure for generated MCP servers.

## Features

- **Auto Deployment**: Pushes builds to MCPGR hosting  
- **Infrastructure as Code**: Terraform for GitHub repo management
- **FastMCP Integration**: Links to fastmcp.cloud for deployment
- **Health Monitoring**: Basic health checks and monitoring

## Components

- `deployer.py` - Handles deployment to hosting platforms
- `terraform/` - Infrastructure definitions for GitHub repos  
- `monitor.py` - Health monitoring and status checks
- `config.py` - Deployment configuration management

## Deployment Flow

1. Build completes in pipeline
2. Code pushed to new GitHub repository (via Terraform)
3. Repository linked to fastmcp.cloud
4. Auto-deployment triggered
5. Health checks verify deployment
6. User notified via email
