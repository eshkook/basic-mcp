"""
Pydantic models for data validation and serialization.
"""

from typing import List, Dict, Any, Optional, Literal, Callable, Awaitable
from pydantic import BaseModel, Field, ConfigDict, field_validator, constr
import os

# Tool Input Models
class LlmCallInput(BaseModel):
    """Validated input for an LLM call."""
    
    # 1. user_answer restriction
    prompt: constr(strip_whitespace=True, max_length=int(os.getenv('LLM_SUBTASK_CHARACTER_LIMIT'))) = Field(
        ...,
        description="prompt for an llm subtask call. Must not exceed characters limit."
    )

