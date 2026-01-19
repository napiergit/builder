# LLM Integration Module

Handles code generation for MCP servers with guardrails and validation.

## Features

- **API Analysis**: Automatically discovers and analyzes platform APIs
- **Code Generation**: Creates MCP server implementations using guardrails
- **Validation**: Tests generated code against requirements
- **Iterative Improvement**: Refines code until tests pass

## Components

- `code_generator.py` - Main LLM integration with guardrails
- `api_analyzer.py` - Platform API discovery and analysis
- `guardrails.py` - Safety and quality constraints
- `validator.py` - Code validation and testing
