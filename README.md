# MCP Builder POC Prototype

An automated system for building MCP (Model Context Protocol) servers from user requirements.

## Architecture

- **builder/**: MCP Builder server with OAuth, viability checking, and build triggering
- **cookiecutter/**: Template framework for generating consistent MCP servers  
- **llm/**: LLM integration with guardrails for code generation
- **store/**: Storage for builds organized by user/platform/version
- **host/**: Deployment infrastructure and hosting setup
- **tests/**: Test suite for validation

## Prototype Features

- OAuth-protected MCP server builder
- API viability assessment 
- Automated MCP server generation
- Version management
- Deployment to fastmcp.cloud

## Getting Started

Each component has its own folder with specific setup instructions.
