"""
OAuth configuration for {{cookiecutter.platform_name}} integration.
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

{% if cookiecutter.include_oauth == "yes" -%}
{% if cookiecutter.oauth_provider == "google" -%}
# Google API scopes
OAUTH_SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
]
{%- else -%}
# OAuth scopes for {{cookiecutter.platform_name}}
OAUTH_SCOPES = [
    'read',
    'write'
]
{%- endif %}

class OAuthConfig:
    """Configuration for OAuth authentication."""
    
    def __init__(self):
        self.client_id = "{{cookiecutter.client_id}}"
        self.client_secret = "{{cookiecutter.client_secret}}"
        self.redirect_uri = "{{cookiecutter.redirect_url}}"
        self.token_storage_path = Path('./.oauth_tokens')
        
    def is_configured(self) -> bool:
        """Check if OAuth is properly configured."""
        return bool(self.client_id and self.client_secret)
    
    def save_token(self, token_data: Dict[str, Any], user_id: str = "default") -> None:
        """Save OAuth token to storage."""
        try:
            self.token_storage_path.mkdir(parents=True, exist_ok=True)
            token_file = self.token_storage_path / f"{user_id}_token.json"
            
            with open(token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            logger.info(f"Token saved for user: {user_id}")
        except (OSError, PermissionError) as e:
            logger.warning(f"Cannot save token to filesystem: {e}")
    
    def load_token(self, user_id: str = "default") -> Optional[Dict[str, Any]]:
        """Load OAuth token from storage."""
        try:
            token_file = self.token_storage_path / f"{user_id}_token.json"
            
            if not token_file.exists():
                return None
            
            with open(token_file, 'r') as f:
                return json.load(f)
        except (OSError, PermissionError) as e:
            logger.debug(f"Cannot load token from filesystem: {e}")
            return None

# Global config instance
oauth_config = OAuthConfig()
{%- else -%}
# OAuth not included in this project
oauth_config = None
{%- endif %}
