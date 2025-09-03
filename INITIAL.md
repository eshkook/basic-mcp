# Currency Converter Feature - USD to EUR

## Feature Description
Add a currency conversion tool to the existing MCP server that converts US Dollars (USD) to Euros (EUR). This feature should be implemented as an MCP tool that can be called by clients to perform real-time currency conversion.

## Requirements
- **Tool Name**: `convert_usd_to_eur`
- **Input**: USD amount as a float/number
- **Output**: Converted EUR amount with current exchange rate
- **Exchange Rate Source**: Use a reliable API or fallback to a reasonable static rate
- **Error Handling**: Handle invalid inputs, API failures, and network issues
- **Integration**: Follow existing MCP tool patterns in the codebase

## Technical Specifications

### MCP Tool Implementation
```python
@mcp.tool("convert_usd_to_eur")
def convert_usd_to_eur(amount: float) -> dict:
    """
    Convert USD to EUR using current exchange rates
    
    Args:
        amount: USD amount to convert
        
    Returns:
        Dictionary with conversion details including rate and result
    """
    # Implementation here
    pass
```

### Expected Response Format
```json
{
    "usd_amount": 100.0,
    "eur_amount": 85.32,
    "exchange_rate": 0.8532,
    "timestamp": "2025-09-03T12:00:00Z",
    "source": "exchange_api"
}
```

## Code Examples
Based on the existing codebase structure in `app.py`, the tool should follow the same pattern as other MCP tools:

```python
# Example similar to existing tools in app.py
@mcp.tool("existing_tool_example")  
def some_existing_tool():
    return {"result": "data"}
```

## Integration Points
- Add to existing FastAPI MCP server in `app.py`
- Follow the same decorator pattern as other tools
- Ensure proper error handling and logging
- Add appropriate dependencies to `requirements.txt` if needed

## Validation Requirements
- Test with various USD amounts (positive, zero, negative)
- Test API failure scenarios
- Verify response format matches specification  
- Test integration with MCP client calls
- Ensure proper error messages for invalid inputs

## Documentation Links
- Existing MCP tools in `/mcp/tools` endpoint
- FastMCP library documentation for tool decorators
- Current `app.py` implementation patterns

## Specific Considerations
- Use environment variables for API keys if external service is used
- Implement rate limiting if using external API
- Consider caching exchange rates for a reasonable period
- Maintain consistency with existing code style and error handling patterns
- Ensure the tool appears in the `/mcp/tools` endpoint listing