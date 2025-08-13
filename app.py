from fastapi import FastAPI
from fastmcp import FastMCP
from fastmcp.types import Tool, Resource, Prompt
from typing import Dict, Any

app = FastAPI(title="Text Assistant MCP Server", version="1.0.0")

# Initialize FastMCP
mcp = FastMCP("text-assistant-mcp")

# Define tools
@mcp.tool("count_words")
def count_words(text: str) -> int:
    """Returns the number of words in the given text."""
    return len(text.split())

@mcp.tool("to_uppercase")
def to_uppercase(text: str) -> str:
    """Converts the input text to uppercase."""
    return text.upper()

# Define resources
@mcp.resource("example-text")
def get_example_text() -> str:
    """A sample paragraph of text that agents can read."""
    return "The quick brown fox jumps over the lazy dog. This sentence contains every letter of the alphabet."

# Define prompts
@mcp.prompt("summarize_prompt")
def summarize_prompt(language: str, text: str) -> str:
    """Allows the agent to generate a summary in the desired language by filling in `language` and `text`."""
    return f"Summarize the following text in {language}:\n\n{text}"

# Include MCP routes in FastAPI app
app.include_router(mcp.router)

@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "healthy", "service": "Text Assistant MCP Server"}

# Add prompt endpoint for HTTP access
@app.post("/prompt/{prompt_name}")
async def get_prompt(prompt_name: str, arguments: Dict[str, Any]):
    """Get prompt content with filled arguments."""
    try:
        if prompt_name == "summarize_prompt":
            language = arguments.get("language", "English")
            text = arguments.get("text", "")
            content = summarize_prompt(language, text)
            return {"prompt": content, "name": prompt_name, "arguments": arguments}
        else:
            return {"error": f"Unknown prompt: {prompt_name}"}, 400
    except Exception as e:
        return {"error": str(e)}, 400

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
