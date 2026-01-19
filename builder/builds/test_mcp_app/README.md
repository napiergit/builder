# Test MCP App

MCP server with OAuth integration

## Features

- **MCP Server**: Built with FastMCP framework
- **OAuth Integration**: Google OAuth 2.0 with Gmail API support
- **Token Management**: Secure token storage and refresh handling
- **Dynamic Client Registration**: RFC 7591 compliant client registration
- **Production Ready**: Proper error handling and logging

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -e .
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your OAuth credentials
   ```

3. **Configure OAuth**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Web application)
   - Set authorized redirect URIs to: `https://your-server.com/oauth/callback`
   - Copy Client ID and Client Secret to `.env` file

4. **Run the Server**
   ```bash
   test_mcp_app
   ```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | Yes |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | Yes |
| `GOOGLE_OAUTH_CALLBACK_URL` | OAuth callback URL | Yes |
| `MCP_SERVER_BASE_URL` | Server base URL | No |
| `TOKEN_STORAGE_PATH` | Token storage directory | No |
| `CLIENT_REGISTRY_PATH` | Client registry storage | No |

## Available Tools

### Authentication
- `get_auth_status()` - Check OAuth authentication status

### Email
- `send_email(to, subject, body, cc="", bcc="")` - Send emails via Gmail

## OAuth Flow

1. **Initial Setup**: Configure OAuth credentials in environment
2. **Authentication**: Use `get_auth_status()` to get auth URL if not authenticated
3. **Token Storage**: Tokens are automatically stored and refreshed
4. **API Access**: Tools automatically use stored or provided tokens

## Development

### Project Structure
```
test_mcp_app/
├── src/
│   ├── __init__.py
│   ├── server.py          # Main MCP server
│   ├── oauth_config.py    # OAuth configuration
│   ├── api_client.py      # Gmail client
│   └── client_registry.py # Dynamic client registration
├── .env.example           # Environment template
├── pyproject.toml         # Project configuration
└── README.md             # This file
```

### Adding New Tools

1. Add tool function to `src/server.py`:
   ```python
   @mcp.tool()
   async def my_tool(param: str) -> Dict[str, Any]:
       """Tool description."""
       # Implementation here
       return {"result": "success"}
   ```

2. Use OAuth authentication if needed:
   ```python
   client = GmailClient()
   if not client.is_authenticated():
       return {"error": "Authentication required"}
   ```

## Deployment

### FastMCP Cloud
```bash
# Deploy to FastMCP cloud
fastmcp deploy
```

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

CMD ["test_mcp_app"]
```

## Security Notes

- Tokens are stored locally in `.oauth_tokens/` directory
- Client secrets are hashed before storage
- Dynamic client registration supports secure client management
- Always use HTTPS in production
- Keep `.env` file secure and never commit to version control

## Troubleshooting

### Authentication Issues
1. Verify OAuth credentials in `.env`
2. Check redirect URI configuration
3. Ensure required scopes are granted

### Token Refresh Problems
1. Check if refresh token is available
2. Verify token hasn't been revoked
3. Re-authenticate if necessary

### Gmail API Issues
1. Ensure Gmail API is enabled in Google Cloud Console
2. Check OAuth scopes include Gmail permissions
3. Verify "Less secure app access" settings if needed

## License

MIT License - see LICENSE file for details.
