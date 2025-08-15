from fastapi import FastAPI
from fastmcp import FastMCP
from typing import Dict, Any
import os
import uvicorn
import logging

logger = logging.getLogger(__name__)

# Application configuration
APP_HOST = os.getenv("APP_HOST")
APP_PORT = int(os.getenv("APP_PORT"))
LOG_LEVEL = os.getenv("LOG_LEVEL")
DEBUG = os.getenv("DEBUG")

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Set debug level for our module during development
if DEBUG == "true":
    logger.setLevel(logging.DEBUG)

app = FastAPI(title="Text Assistant MCP Server", version="1.0.0")

# Initialize FastMCP
mcp = FastMCP("text-assistant-mcp")

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
@mcp.resource("mcp://text-assistant/resources/example-text")
def get_example_text() -> str:
    """A sample paragraph of text that agents can read."""
    resource_path = os.path.join(BASE_DIR, "resources", "example-text.txt")
    with open(resource_path, "r") as f:
        return f.read().strip()

# Define prompts
@mcp.prompt("summarize_prompt")
def summarize_prompt(language: str, text: str) -> str:
    """Allows the agent to generate a summary in the desired language by filling in `language` and `text`."""
    prompt_path = os.path.join(BASE_DIR, "prompts", "summarize_prompt.txt")
    with open(prompt_path, "r") as f:
        template = f.read().strip()
    return template.format(language=language, text=text)

@app.get("/health")
def health_check() -> Dict[str, str]:
    logger.info(f"INFO LOGGING")
    logger.debug(f"DEBUG LOGGING")
    return {"status": "healthy", "service": "Text Assistant MCP Server"}

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host=APP_HOST, 
        port=APP_PORT, 
        log_level=LOG_LEVEL.lower()
    )
