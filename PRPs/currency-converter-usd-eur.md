# Project Requirements & Planning (PRP): USD to EUR Currency Converter

## Overview
Implement a robust USD to EUR currency conversion tool as an MCP (Model Context Protocol) tool in the existing FastAPI-based MCP server. This tool will provide real-time exchange rates with proper error handling, caching, and fallback mechanisms.

## Context Analysis

### Existing Codebase Patterns
Based on analysis of `/app.py:33-41`, the current MCP tool implementation pattern is:

```python
@mcp.tool("count_words")
def count_words(text: str) -> int:
    """Returns the number of words in the given text."""
    return len(text.split())
```

**Key Patterns to Follow:**
- Simple `@mcp.tool("tool_name")` decorator
- Clear docstring with functionality description
- Type hints for parameters and return values
- Direct return of simple types or dictionaries

### Current Dependencies (`requirements.txt`)
Available dependencies:
- `fastapi>=0.104.1`
- `uvicorn[standard]>=0.24.0` 
- `fastmcp>=0.1.0`
- `pydantic>=2.5.0`
- `numpy>=1.24.3`

**Missing Dependencies to Add:**
- `httpx>=0.25.0` - for async HTTP requests to currency APIs
- `pytest>=7.0.0` - for testing (no current test framework found)

### Testing Strategy
No existing test patterns found in codebase. Will need to establish pytest-based testing approach.

## External Research & Documentation

### FastMCP Library Documentation
- **Primary Documentation**: https://gofastmcp.com/getting-started/welcome
- **GitHub Repository**: https://github.com/jlowin/fastmcp
- **Key Feature**: FastMCP 2.0 provides high-level decorators that abstract complex protocol handling

### Recommended Currency APIs (in order of reliability)

1. **ExchangeRate-API** (Primary)
   - URL: `https://api.exchangerate-api.com/v4/latest/USD`
   - Features: 99.99% uptime, free tier, 60-second updates
   - No API key required for basic usage
   - Data sourced from European Central Bank

2. **Fixer.io** (Fallback #1) 
   - URL: `http://data.fixer.io/api/latest?access_key={key}&symbols=EUR&base=USD`
   - Features: 60-second updates, requires free API key
   - Reliable commercial provider

3. **ExchangeRatesAPI.io** (Fallback #2)
   - URL: `https://api.exchangeratesapi.io/v1/latest?access_key={key}&symbols=EUR&base=USD`
   - Features: 60-minute updates, requires API key

### Currency Conversion Best Practices
Based on research from multiple sources:

**Error Handling:**
- Implement try-catch blocks for network failures
- Validate HTTP status codes before processing
- Provide informative error messages
- Log errors for monitoring

**Caching Strategy:**
- Cache exchange rates for 5-10 minutes to reduce API calls
- Use time-based expiration
- Store last successful rate as fallback

**Fallback Mechanisms:**
- Multiple API sources with automatic failover
- Use cached historical rate if all APIs fail
- Provide reasonable default rate as last resort

## Implementation Blueprint

### Core Function Structure
```python
@mcp.tool("convert_usd_to_eur")
async def convert_usd_to_eur(amount: float) -> dict:
    """
    Convert USD to EUR using current exchange rates
    
    Args:
        amount: USD amount to convert (must be >= 0)
        
    Returns:
        Dictionary with conversion details including rate and result
        
    Raises:
        ValueError: For invalid input amounts
        HTTPException: For API failures with no fallback available
    """
    # Implementation here
    pass
```

### Response Format (as specified in INITIAL.md)
```json
{
    "usd_amount": 100.0,
    "eur_amount": 85.32,
    "exchange_rate": 0.8532,
    "timestamp": "2025-09-03T12:00:00Z",
    "source": "exchangerate-api"
}
```

### Error Handling Strategy
1. **Input Validation**: Check for negative amounts, non-numeric values
2. **API Failures**: Try primary API → fallback API → cached rate → default rate
3. **Network Timeouts**: 10-second timeout per API call
4. **Rate Limiting**: Respect API rate limits with exponential backoff

### Caching Implementation
```python
# Simple in-memory cache with timestamp
_exchange_cache = {
    "rate": None,
    "timestamp": None,
    "ttl_minutes": 10
}
```

### Environment Configuration
```bash
# Optional API keys for fallback services
FIXER_API_KEY=your_fixer_key_here
EXCHANGERATES_API_KEY=your_key_here

# Cache TTL in minutes (default: 10)
CURRENCY_CACHE_TTL=10

# Fallback rate if all APIs fail (default: 0.85)
USD_EUR_FALLBACK_RATE=0.85
```

## Implementation Tasks (Execution Order)

1. **Add Dependencies** 
   - Add `httpx>=0.25.0` to `requirements.txt`
   - Add `pytest>=7.0.0` for testing

2. **Implement Core Function**
   - Create `convert_usd_to_eur` function with `@mcp.tool` decorator
   - Implement input validation for amount parameter
   - Add proper type hints and docstring

3. **Add HTTP Client Setup**
   - Create async httpx client with proper timeouts
   - Configure user agent and headers

4. **Implement Primary API Integration**
   - ExchangeRate-API integration with error handling
   - Parse JSON response and extract USD→EUR rate

5. **Add Caching Layer**
   - Simple in-memory cache with timestamp validation
   - TTL-based expiration logic

6. **Implement Fallback Strategy**
   - Try multiple APIs in sequence on failure
   - Use cached rate if available
   - Final fallback to environment-configured rate

7. **Add Comprehensive Error Handling**
   - Input validation with clear error messages
   - Network error handling with retry logic
   - Logging for monitoring and debugging

8. **Create Response Formatter**
   - Structure response according to specified JSON format
   - Include metadata (timestamp, source, rate used)

9. **Write Unit Tests**
   - Test successful conversion scenarios
   - Test input validation (negative amounts, invalid types)
   - Test API failure scenarios and fallbacks
   - Test caching behavior

10. **Integration Testing**
    - Test tool registration in MCP server
    - Verify tool appears in `/mcp/tools` endpoint
    - Test actual MCP client calls

## Code References

### Files to Study for Patterns
- `/app.py:33-41` - Existing MCP tool patterns
- `/app.py:24-27` - FastMCP initialization pattern  
- `/app.py:11-23` - Environment variable and logging setup

### Integration Points
- Add new tool function in `app.py` after line 41
- Follow same decorator and docstring pattern as `count_words` and `to_uppercase`
- Use existing logging setup from lines 8-23

## Validation Gates (Must Pass)

### Dependency Installation
```bash
# Install new dependencies
pip install httpx>=0.25.0 pytest>=7.0.0
```

### Unit Tests (Pytest)
```bash
# Run all tests
pytest tests/test_currency_converter.py -v

# Test specific scenarios
pytest tests/test_currency_converter.py::test_valid_conversion -v
pytest tests/test_currency_converter.py::test_api_failure_fallback -v
pytest tests/test_currency_converter.py::test_invalid_input -v
```

### Integration Testing
```bash
# Start the server
python app.py

# Verify tool is registered
curl http://localhost:5000/mcp/tools

# Test tool execution
curl -X POST http://localhost:5000/mcp/tools/convert_usd_to_eur \
  -H "Content-Type: application/json" \
  -d '{"amount": 100.0}'
```

### Code Quality
```bash
# Format and lint (if available)
black app.py tests/
ruff check app.py tests/

# Type checking (if mypy available)  
mypy app.py
```

## Error Scenarios & Handling

### Input Validation Errors
- Negative amounts → Return error with message
- Non-numeric input → Return error with message
- Extremely large amounts → Consider reasonable limits

### API Failure Scenarios
- Network timeout → Try fallback API
- Invalid response format → Try fallback API
- Rate limit exceeded → Use cached rate or wait
- All APIs down → Use last cached rate or fallback constant

### Expected Response on Errors
```json
{
    "error": "Invalid input: amount must be a positive number",
    "error_code": "INVALID_INPUT"
}
```

## Gotchas & Considerations

### API Specific Issues
- **ExchangeRate-API**: Free tier has rate limits, no API key needed
- **Fixer.io**: Requires free API key registration
- **Rate Limiting**: Some APIs limit requests per minute/hour

### Implementation Considerations
- **Async Operations**: Use async/await for HTTP requests to avoid blocking
- **Timeout Handling**: Set reasonable timeouts (10 seconds) for API calls
- **Memory Usage**: Keep cache size reasonable, implement cleanup if needed
- **Logging**: Log API failures and fallback usage for monitoring

### FastMCP Specific
- Tools must be async if they make external API calls
- Return dictionaries are automatically serialized to JSON
- Exceptions are caught and returned as error responses to MCP clients

## Success Criteria

### Functional Requirements
- ✅ Convert valid USD amounts to EUR with current rates
- ✅ Handle invalid inputs gracefully with clear error messages
- ✅ Implement fallback strategy for API failures
- ✅ Cache rates to reduce API calls
- ✅ Return structured response matching specification

### Non-Functional Requirements
- ✅ Response time under 5 seconds (including fallbacks)
- ✅ Handle concurrent requests without race conditions
- ✅ Proper error logging for debugging
- ✅ Follow existing codebase patterns and conventions

### Integration Requirements
- ✅ Tool appears in MCP tools listing
- ✅ Can be called by MCP clients
- ✅ Maintains existing server functionality

## Quality Assessment

**PRP Confidence Score: 9/10**

This PRP provides comprehensive context for one-pass implementation success because:

✅ **Complete Context**: Includes existing patterns, dependencies, and external research  
✅ **Clear Implementation Path**: Step-by-step tasks with specific code examples  
✅ **Robust Error Handling**: Multiple fallback strategies with specific scenarios  
✅ **Validation Strategy**: Executable tests and integration checks  
✅ **External References**: Specific API documentation and best practices  
✅ **Pattern Consistency**: Follows existing codebase conventions  

**Potential Risk Areas:**
- API key management for fallback services (mitigated with environment variables)
- Cache invalidation edge cases (mitigated with simple TTL approach)

The comprehensive research and clear implementation blueprint should enable successful one-pass implementation by Claude Code.