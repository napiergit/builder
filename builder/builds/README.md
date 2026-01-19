# Build Storage Structure

Organized storage for generated MCP servers by user, platform, and version.

## Directory Structure

```
builds/
├── {user-uuid}/
│   ├── {platform}/
│   │   ├── 1/
│   │   │   ├── prompt.txt          # Original build request
│   │   │   ├── mcp/                # Generated MCP server code
│   │   │   │   ├── server.py
│   │   │   │   ├── requirements.txt
│   │   │   │   └── test_server.py
│   │   │   ├── metadata.json       # Build metadata
│   │   │   └── deployment.json     # Deployment info
│   │   ├── 2/                      # Next version
│   │   └── ...
│   └── {another-platform}/
└── {another-user-uuid}/
```

## Version Management

- Each build creates a new version
- Versions are sequential integers starting from 1
- Each version contains complete, independent MCP server
- Previous versions are preserved for rollback/comparison
