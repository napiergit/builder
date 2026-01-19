# Builder Component Requirements

## Interpretation of Overall System Requirements

The Builder component serves as the **main MCP server interface** that users interact with to request MCP server builds.

### Key Responsibilities

1. **OAuth Authentication**: Behind OAuth with email -> UUID mapping as specified
2. **Two Core Tools Implementation**:
   - `is_building_mcp_server_viable`: Platform viability assessment
   - `build_mcp_server`: Initiates the complete build pipeline

### Implementation Details

- **Prerequisites**: Cookie cutter app with OAuth (implemented via template system)
- **Tests**: OAuth functionality validation (implemented in test suite)
- **GitHub Deployment**: Ability to deploy to GitHub (handled by pipeline integration)

### Platform Assessment Logic

- Returns required OAuth parameters (client_id, client_secret, redirect_url)
- Assesses API viability for known platforms
- Logs feature requests for unsupported platforms

### Build Pipeline Trigger

- Validates all required parameters before proceeding
- Creates build directory structure as specified: `builds/<uuid>/<platform>/<version>/`
- Triggers async pipeline execution
- Returns immediate response to user with build ID

### Version Management

- Each build call creates new version (incremental integers)
- Previous versions preserved for context and rollback
- LLM integration considers all previous versions as specified
