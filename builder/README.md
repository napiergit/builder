# MCP Builder Server

OAuth-protected MCP server that provides tools for building new MCP servers.

## Features

- **OAuth Authentication**: Email-based authentication with UUID mapping
- **Viability Assessment**: Checks if an MCP server can be built for a given platform
- **Build Tool**: Triggers the pipeline to build and deploy MCP servers

## Tools

1. `is_building_mcp_server_viable` - Assesses API viability and returns required OAuth parameters
2. `build_mcp_server` - Builds and deploys an MCP server for the specified platform

## Authentication

Uses OAuth with email -> UUID mapping for user identification.
