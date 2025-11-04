import os
import re
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import asyncio
from string import Template

from pydantic_ai import Agent, RunContext

from ..prompts import (
    DROP_FEATURE_DUPS_SYSTEM_PROMPT
)
from ..providers import get_llm_model_for_agent
from ..models import (
    AgentDependencies
)

logger = logging.getLogger(__name__)

system_prompt=Template(DROP_FEATURE_DUPS_SYSTEM_PROMPT).substitute(
    clarifications_allowed=os.getenv('DROP_FEATURE_DUPS_CLARIFICATIONS')
)

# Initialize the agent with flexible model configuration
drop_feature_dups_agent = Agent(
    get_llm_model_for_agent(model_choice=os.getenv('DROP_FEATURE_DUPS_AGENT_LLM_CHOICE')),
    deps_type=AgentDependencies,
    system_prompt=system_prompt
)


@drop_feature_dups_agent.tool
async def ask_user_a_question(
    ctx: RunContext[AgentDependencies],
    question_for_user: str,
) -> str:
    """
    Ask the user for clarification about the features.

    This tool prompts the user with a clarifying question,
    collects their response, and then returns this new information.

    Args:
        question_for_user: The clarification question the agent wants to ask the user.

    Returns:
        The user's clarification. 
    """

    # 1️⃣ Send request to client
    await ctx.deps.send_func({
        "type": "user-input-request",
        "content": question_for_user
    })

    user_clarification = await ctx.deps.user_reply_queue.get()

    return user_clarification 