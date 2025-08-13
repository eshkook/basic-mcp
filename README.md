# Text Assistant MCP Server

A minimal MCP (Model Context Protocol) compatible server that provides simple tools, resources, and prompt templates for text processing. Built with FastAPI and FastMCP for seamless integration.

## Features

### 🔹 Resources
- **`/resources/example-text`**
  - Description: A sample paragraph of text that agents can read.
  - Content: "The quick brown fox jumps over the lazy dog. This sentence contains every letter of the alphabet."
  - File: `resources/example-text.txt`

### 🔹 Tools
1. **`count_words(text: str) -> int`**
   - Description: Returns the number of words in the given text.
   - Input: `{"text": "your text here"}`

2. **`to_uppercase(text: str) -> str`**
   - Description: Converts the input text to uppercase.
   - Input: `{"text": "your text here"}`

### 🔹 Prompts
1. **`summarize_prompt(language: str, text: str)`**
   - Template: "Summarize the following text in {language}:\n\n{text}"
   - Description: Allows the agent to generate a summary in the desired language by filling in `language` and `text`.
   - File: `prompts/summarize_prompt.txt`

## Behavior
- The MCP server does not maintain memory.
- The agent is responsible for discovering and choosing tools, reading resources, and filling in prompts.
- If a tool uses an LLM internally (e.g. in future expansions), the MCP server would pay for that usage.

## Installation & Setup

### Prerequisites
- Docker and Docker Compose

### Docker Deployment
1. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

2. For debugging with VS Code:
   ```bash
   # Set DEBUG=true in .env file
   docker-compose up --build
   # Then attach debugger in VS Code
   ```

## Usage

### FastAPI Endpoints
- `GET /health` - Health check endpoint
- `GET /mcp/tools` - List available MCP tools
- `POST /mcp/tools/{tool_name}` - Execute MCP tools
- `GET /mcp/resources` - List available MCP resources
- `GET /mcp/resources/{resource_name}` - Read MCP resources
- `GET /mcp/prompts` - List available MCP prompts

### MCP Protocol
The server implements the Model Context Protocol using FastMCP and can be used with MCP-compatible clients.

#### Example MCP Client Configuration
```json
{
  "mcpServers": {
    "text-assistant": {
      "command": "docker",
      "args": ["run", "--rm", "my-fastapi-app:1.0.0"],
      "env": {}
    }
  }
}
```

## Development

### Project Structure
```
basic-mcp/
├── app.py              # FastAPI application with FastMCP integration
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker container definition
├── docker-compose.yml # Docker Compose configuration
├── entrypoint.sh      # Container startup script
├── resources/         # Static resources
│   └── example-text.txt
├── prompts/           # Prompt templates
│   └── summarize_prompt.txt
├── .vscode/           # VS Code configuration
│   └── launch.json    # Debug configuration
└── README.md          # This file
```

### Debugging
1. Set `DEBUG=true` in your `.env` file
2. Start the container: `docker-compose up --build`
3. In VS Code, use "Attach to Docker Container" configuration
4. Set breakpoints and debug the FastAPI application

### Adding New Features
- **Tools**: Add new functions with `@mcp.tool("tool_name")` decorator
- **Resources**: Add new files to the `resources/` directory
- **Prompts**: Add new template files to the `prompts/` directory

## License
This project is open source and available under the MIT License.
