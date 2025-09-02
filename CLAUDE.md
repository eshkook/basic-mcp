# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Docker Development
- **Development**: `docker-compose -f docker-compose.dev.yml up --build` (runs with hot reload and debug port 5678)
- **Production**: `docker-compose -f docker-compose.prod.yml up --build`
- **Health check**: `curl http://localhost:5000/health`

### Environment Configuration
- Set `DEBUG=true` in `.env` for debug mode
- Set `MODE=api` for FastAPI server, `MODE=script` for script execution
- Set `LOG_LEVEL` (default levels: DEBUG, INFO, WARNING, ERROR)

### VS Code Debugging
1. Set `DEBUG=true` in `.env`
2. Run `docker-compose -f docker-compose.dev.yml up --build`
3. Use "Attach to Docker Container" launch configuration (port 5678)

## Architecture

### MCP Server Implementation
This is a FastAPI-based MCP (Model Context Protocol) server using the FastMCP library. The application provides:

- **Tools**: Functions that can be called by MCP clients (decorated with `@mcp.tool()`)
- **Resources**: Static content accessible via MCP URIs (decorated with `@mcp.resource()`)  
- **Prompts**: Template-based prompts with variable substitution (decorated with `@mcp.prompt()`)

### Core Structure
- `app.py`: Main FastAPI application with MCP integration
- `script.py`: Simple standalone script
- `resources/`: Static files served as MCP resources
- `prompts/`: Template files for MCP prompts
- `entrypoint.sh`: Dual-mode container entry point (API/script)

### MCP Endpoints
- `GET /mcp/tools` - List available tools
- `POST /mcp/tools/{tool_name}` - Execute tools
- `GET /mcp/resources` - List resources
- `GET /mcp/resources/{resource_name}` - Read resources
- `GET /mcp/prompts` - List prompts

### Adding Features
- **New tools**: Add functions with `@mcp.tool("name")` decorator in `app.py`
- **New resources**: Add files to `resources/` and create corresponding `@mcp.resource()` functions
- **New prompts**: Add template files to `prompts/` and create `@mcp.prompt()` functions

### Container Modes
The entrypoint script supports two execution modes via `MODE` environment variable:
- `MODE=api`: Runs FastAPI server on port 5000
- `MODE=script`: Executes standalone Python script