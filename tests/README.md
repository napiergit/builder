# Test Suite

Comprehensive testing for the MCP Builder system components.

## Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing  
- **End-to-End Tests**: Full workflow testing
- **Security Tests**: OAuth and security validation
- **Performance Tests**: Load and stress testing

## Test Structure

```
tests/
├── unit/
│   ├── test_builder_server.py     # Builder MCP server tests
│   ├── test_code_generator.py     # LLM integration tests
│   ├── test_api_analyzer.py       # API analysis tests
│   ├── test_guardrails.py         # Security guardrails tests
│   └── test_validator.py          # Code validation tests
├── integration/
│   ├── test_build_pipeline.py     # Full build pipeline tests
│   └── test_oauth_flow.py         # OAuth integration tests
├── e2e/
│   └── test_complete_workflow.py  # End-to-end workflow tests
└── fixtures/
    ├── sample_platforms.json      # Test platform configurations
    └── sample_code.py             # Test code samples
```
