# MCP Builder Setup Guide

Complete setup instructions for the MCP Builder POC prototype system.

## Prerequisites

- Python 3.9+
- GitHub account with personal access token
- FastMCP.cloud account and API key
- Terraform installed (for infrastructure management)

## Environment Variables

Create a `.env` file in the project root:

```bash
# GitHub Configuration
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_ORG=your_github_org_name

# FastMCP Configuration  
FASTMCP_API_KEY=your_fastmcp_api_key

# LLM Configuration (choose one)
LLM_ENDPOINT=http://localhost:11434  # For local Ollama
# OPENAI_API_KEY=your_openai_api_key  # For OpenAI
# ANTHROPIC_API_KEY=your_anthropic_key  # For Claude

```

## Installation

1. **Clone and Install Dependencies**
```bash
git clone <repository-url>
cd mcp-builder
pip install -r requirements.txt
```

2. **Setup Terraform for GitHub Management**
```bash
cd host/terraform
terraform init
```

3. **Configure FastMCP.cloud Integration**
- Create account at https://fastmcp.cloud
- Generate API key from dashboard
- Add to environment variables

## Running the System

### Start the MCP Builder Server

```bash
cd builder
python server.py
```

The server will be available as an MCP server that can be connected to your MCP client.

### Available Tools

The builder provides two main tools:

1. **`is_building_mcp_server_viable`**
   - Check if building an MCP server for a platform is possible
   - Returns required OAuth parameters

2. **`build_mcp_server`**
   - Initiates the full build and deployment pipeline
   - Creates GitHub repo, generates code, deploys to FastMCP.cloud

## Development Setup

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=. tests/
```

### Code Quality

```bash
# Format code
black .

# Type checking
mypy .

# Linting
flake8 .

# Import sorting
isort .
```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │───▶│  Builder Server │───▶│   Pipeline      │
│                 │    │   (OAuth + API) │    │  Orchestrator   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Code Gen      │◀───│   API Analyzer  │
                       │  (LLM + Guard)  │    │   (Platform)    │
                       └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Validator     │    │   Deployer      │
                       │  (Tests + QA)   │───▶│  (GitHub + MCP) │
                       └─────────────────┘    └─────────────────┘
```

## Usage Example

1. **Connect MCP Client to Builder Server**
```json
{
  "mcpServers": {
    "mcp-builder": {
      "command": "python",
      "args": ["/path/to/builder/server.py"]
    }
  }
}
```

2. **Check Platform Viability**
```
Tool: is_building_mcp_server_viable
Args: {
  "platform": "github",
  "user_email": "your@email.com"
}
```

3. **Build MCP Server**
```
Tool: build_mcp_server  
Args: {
  "platform": "github",
  "user_email": "your@email.com",
  "client_id": "your_github_oauth_id",
  "client_secret": "your_github_oauth_secret", 
  "redirect_url": "http://localhost:8080/callback",
  "description": "GitHub repository management MCP server"
}
```

## Supported Platforms

Currently supported platforms:
- GitHub (repositories, issues, users)
- Gmail (email management)
- Slack (messaging, channels)
- Notion (pages, databases)
- Twitter (tweets, users)

## Troubleshooting

### Common Issues

1. **GitHub API Rate Limits**
   - Ensure GitHub token has correct permissions
   - Check rate limit status in GitHub settings

2. **FastMCP Deployment Failures**
   - Verify API key is valid
   - Check repository is public (required for FastMCP)

3. **LLM Generation Errors**
   - Check LLM endpoint configuration
   - Verify API keys for cloud LLM services

4. **OAuth Configuration**
   - Ensure OAuth credentials are properly configured
   - Check redirect URLs match exactly

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python server.py
```

### Build Directory Structure

Generated builds are stored in:
```
builds/
├── {user-uuid}/
│   └── {platform}/
│       └── {version}/
│           ├── prompt.txt       # Original request
│           ├── metadata.json    # Build metadata  
│           ├── deployment.json  # Deployment info
│           └── mcp/            # Generated code
│               ├── server.py
│               ├── requirements.txt
│               └── test_server.py
```

## Contributing

1. Follow code quality standards (black, mypy, flake8)
2. Add tests for new functionality
3. Update documentation for changes
4. Test with multiple platforms

## Security Considerations

- Never hardcode OAuth secrets in generated code
- Use environment variables for all sensitive data
- Validate all user inputs through guardrails
- Regular security audits of generated code
