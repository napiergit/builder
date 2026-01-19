import os
import sys
import json
import logging
import httpx
import uuid
import secrets
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from fastapi import Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastmcp import FastMCP

# Add current directory to Python path for cloud deployment
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from .oauth_config import OAuthConfig, OAUTH_SCOPES, oauth_config
    from .api_client import GmailClient
    from .client_registry import client_registry
except ImportError:
    # Fallback for cloud deployment
    from api_client import GmailClient
    from oauth_config import OAuthConfig, OAUTH_SCOPES, oauth_config
    from client_registry import client_registry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_mcp_app")

# In-memory storage for OAuth sessions (browser agents)
oauth_sessions = {}

# In-memory storage for MCP token -> OAuth token mapping
mcp_token_store = {}

def get_oauth_token_from_mcp_token(mcp_token: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve OAuth token from MCP token.
    
    Args:
        mcp_token: MCP access token provided by client
        
    Returns:
        OAuth token data if valid, None otherwise
    """
    if not mcp_token:
        return None
        
    token_data = mcp_token_store.get(mcp_token)
    if not token_data:
        return None
        
    return token_data.get("oauth_token")

# Initialize FastMCP server
mcp = FastMCP("Test MCP App")

@mcp.tool()
async def send_email(to: str, subject: str, body: str, cc: str = "", bcc: str = "") -> Dict[str, Any]:
    """
    Send an email via Gmail.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (HTML supported)
        cc: CC recipients (comma-separated, optional)
        bcc: BCC recipients (comma-separated, optional)
        
    Returns:
        Email sending result
    """
    try:
        # Get OAuth token from MCP context
        mcp_token = mcp.get_request_context().get("access_token")
        oauth_token = get_oauth_token_from_mcp_token(mcp_token) if mcp_token else None
        
        if oauth_token:
            # Use on-behalf-of flow
            client = GmailClient(access_token=oauth_token.get("access_token"))
        else:
            # Use stored credentials
            client = GmailClient()
        
        if not client.is_authenticated():
            return {
                "error": "Authentication required",
                "auth_url": client.get_auth_url() if oauth_config.is_configured() else None
            }
        
        result = await client.send_email(
            to=to,
            subject=subject,
            body=body,
            cc=cc if cc else None,
            bcc=bcc if bcc else None,
            is_html=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return {"error": str(e)}

@mcp.tool()
async def get_auth_status() -> Dict[str, Any]:
    """
    Check OAuth authentication status.
    
    Returns:
        Authentication status and configuration info
    """
    try:
        # Check if OAuth is configured
        is_configured = oauth_config.is_configured()
        
        # Check if we have a stored token
        client = GmailClient()
        is_authenticated = client.is_authenticated()
        
        result = {
            "oauth_configured": is_configured,
            "authenticated": is_authenticated,
            "scopes": OAUTH_SCOPES
        }
        
        if is_configured and not is_authenticated:
            result["auth_url"] = client.get_auth_url()
        
        return result
        
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        return {"error": str(e)}

# OAuth callback endpoint
@mcp.get("/oauth/callback")
async def oauth_callback(request: Request):
    """Handle OAuth callback."""
    try:
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        error = request.query_params.get("error")
        
        if error:
            logger.error(f"OAuth error: {error}")
            return HTMLResponse(f"<h1>OAuth Error</h1><p>{error}</p>")
        
        if not code:
            return HTMLResponse("<h1>OAuth Error</h1><p>No authorization code received</p>")
        
        # Exchange code for token
        client = GmailClient()
        token_data = client.exchange_code_for_token(code)
        
        # Store in session for browser-based flows
        session_id = str(uuid.uuid4())
        oauth_sessions[session_id] = {
            "token": token_data,
            "timestamp": datetime.now(),
            "state": state
        }
        
        logger.info("OAuth callback successful")
        return HTMLResponse(f"""
        <h1>Authentication Successful!</h1>
        <p>You can now close this window and return to your application.</p>
        <p>Session ID: {session_id}</p>
        """)
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return HTMLResponse(f"<h1>OAuth Error</h1><p>{str(e)}</p>")

# Dynamic Client Registration endpoints
@mcp.post("/clients")
async def register_client(request: Request):
    """Register a new OAuth client dynamically."""
    try:
        registration_request = await request.json()
        response = client_registry.register_client(registration_request)
        return JSONResponse(response, status_code=201)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        logger.error(f"Client registration error: {e}")
        return JSONResponse({"error": "Internal server error"}, status_code=500)

@mcp.get("/clients/{client_id}")
async def get_client(client_id: str):
    """Get client information."""
    try:
        client_data = client_registry.get_client(client_id)
        if not client_data:
            return JSONResponse({"error": "Client not found"}, status_code=404)
        return JSONResponse(client_data)
    except Exception as e:
        logger.error(f"Get client error: {e}")
        return JSONResponse({"error": "Internal server error"}, status_code=500)

# Health check endpoint
@mcp.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": "Test MCP App",
        "version": "0.1.0"
    })

def main():
    """Main entry point."""
    logger.info("Starting Test MCP App MCP Server")
    
    # Validate configuration
    if not oauth_config.is_configured():
        logger.warning("OAuth not configured - some features may not work")
    
    # Start the server
    mcp.run()

if __name__ == "__main__":
    main()
