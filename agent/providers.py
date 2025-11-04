"""
Flexible provider configuration for LLM.
"""

import os
from openai import AsyncOpenAI

def get_llm_client_for_subtask() -> AsyncOpenAI:
    """
    Get embedding client configuration based on environment variables.
    
    Returns:
        Configured OpenAI-compatible client for embeddings
    """
    base_url = os.getenv('LLM_BASE_URL')
    api_key = os.getenv('LLM_API_KEY')
    
    return AsyncOpenAI(
        base_url=base_url,
        api_key=api_key
    )
