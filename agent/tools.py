"""
Tools.
"""

import traceback
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional, Callable, Awaitable

from .providers import get_llm_client_for_subtask

logger = logging.getLogger(__name__)

async def stream_llm_response(model_choice: str, system_prompt: str, user_prompt: str) -> AsyncGenerator[str, None]:
    try:
        llm_client = get_llm_client_for_subtask()
        stream = await llm_client.chat.completions.create(
            model=model_choice,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield delta
    except Exception as e:
        logger.error(f"Failed to stream LLM response: {e}")
        traceback.print_exc()
        raise


async def refine_text_with_llm(
        model_choice: str, 
        system_prompt: str, 
        user_prompt: str, 
        # send_func: Callable[[Dict[str, Any]], Awaitable[None]] # uncomment when need to stream tokens to client
    ) -> str:
    llm_response = []
    async for chunk in stream_llm_response(model_choice, system_prompt, user_prompt):
        # await send_func({"type": "subtask-llm-text", "content": chunk})
        llm_response.append(chunk)
    return "".join(llm_response)

