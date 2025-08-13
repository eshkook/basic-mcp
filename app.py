from fastapi import FastAPI
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    ReadResourceRequest,
    ReadResourceResult,
    Resource,
    Tool,
    TextContent,
    Prompt,
    ListPromptsRequest,
    ListPromptsResult,
)
from typing import Dict, Any, List
import asyncio
import os

# Create FastAPI app for HTTP endpoints (optional, for health checks)
app = FastAPI(title="Text Assistant MCP Server", version="1.0.0")

@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "healthy", "service": "Text Assistant MCP Server"}

# MCP Server Implementation
class TextAssistantMCPServer:
    def __init__(self):
        self.server = Server("text-assistant-mcp")
        
        # Register handlers
        self.server.list_tools()(self.list_tools)
        self.server.call_tool()(self.call_tool)
        self.server.list_resources()(self.list_resources)
        self.server.read_resource()(self.read_resource)
        self.server.list_prompts()(self.list_prompts)
    
    async def list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """List available tools."""
        tools = [
            Tool(
                name="count_words",
                description="Returns the number of words in the given text.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to count words in."
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="to_uppercase",
                description="Converts the input text to uppercase.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to convert to uppercase."
                        }
                    },
                    "required": ["text"]
                }
            )
        ]
        return ListToolsResult(tools=tools)
    
    async def call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Execute a tool."""
        tool_name = request.name
        arguments = request.arguments
        
        if tool_name == "count_words":
            text = arguments.get("text", "")
            word_count = len(text.split())
            return CallToolResult(
                content=[TextContent(type="text", text=str(word_count))]
            )
        
        elif tool_name == "to_uppercase":
            text = arguments.get("text", "")
            uppercase_text = text.upper()
            return CallToolResult(
                content=[TextContent(type="text", text=uppercase_text)]
            )
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def list_resources(self, request: ListResourcesRequest) -> ListResourcesResult:
        """List available resources."""
        resources = [
            Resource(
                uri="mcp://text-assistant/resources/example-text",
                name="example-text",
                description="A sample paragraph of text that agents can read.",
                mimeType="text/plain"
            )
        ]
        return ListResourcesResult(resources=resources)
    
    async def read_resource(self, request: ReadResourceRequest) -> ReadResourceResult:
        """Read a specific resource."""
        uri = request.uri
        
        if uri == "mcp://text-assistant/resources/example-text":
            content = "The quick brown fox jumps over the lazy dog. This sentence contains every letter of the alphabet."
            return ReadResourceResult(
                contents=[TextContent(type="text", text=content)]
            )
        
        else:
            raise ValueError(f"Unknown resource: {uri}")
    
    async def list_prompts(self, request: ListPromptsRequest) -> ListPromptsResult:
        """List available prompts."""
        prompts = [
            Prompt(
                name="summarize_prompt",
                description="Allows the agent to generate a summary in the desired language by filling in `language` and `text`.",
                arguments={
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "description": "The language to summarize in."
                        },
                        "text": {
                            "type": "string",
                            "description": "The text to summarize."
                        }
                    },
                    "required": ["language", "text"]
                }
            )
        ]
        return ListPromptsResult(prompts=prompts)

# Create MCP server instance
mcp_server = TextAssistantMCPServer()

# Function to get prompt content
def get_prompt_content(name: str, arguments: Dict[str, Any]) -> str:
    """Get the content of a prompt with filled arguments."""
    if name == "summarize_prompt":
        language = arguments.get("language", "English")
        text = arguments.get("text", "")
        return f"Summarize the following text in {language}:\n\n{text}"
    else:
        raise ValueError(f"Unknown prompt: {name}")

# Add prompt endpoint to FastAPI app
@app.post("/prompt/{prompt_name}")
async def get_prompt(prompt_name: str, arguments: Dict[str, Any]):
    """Get prompt content with filled arguments."""
    try:
        content = get_prompt_content(prompt_name, arguments)
        return {"prompt": content, "name": prompt_name, "arguments": arguments}
    except ValueError as e:
        return {"error": str(e)}, 400

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
