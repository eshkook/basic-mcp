import os
import re
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import asyncio
from string import Template

from pydantic_ai import Agent, RunContext

from ..prompts import (
    FEASIBILITY_CHECK_SYSTEM_PROMPT
    # OVERVIEW_REFINEMENT_SYSTEM_PROMPT,
    # OVERVIEW_REFINEMENT_USER_PROMPT
)
from ..providers import get_llm_model_for_agent
from ..tools import (
    refine_text_with_llm
)
from ..models import (
    AgentDependencies,
    LlmCallInput
)


logger = logging.getLogger(__name__)

system_prompt=Template(FEASIBILITY_CHECK_SYSTEM_PROMPT).substitute(
    clarifications_allowed=os.getenv('FEASIBILITY_CHECK_CLARIFICATIONS')
)

# Initialize the agent with flexible model configuration
feasibility_check_agent = Agent(
    get_llm_model_for_agent(model_choice=os.getenv('FEASIBILITY_CHECK_AGENT_LLM_CHOICE')),
    deps_type=AgentDependencies,
    system_prompt=system_prompt
)


@feasibility_check_agent.tool
async def ask_user_a_question(
    ctx: RunContext[AgentDependencies],
    question_for_user: str,
) -> str:
    """
    Ask the user for clarification about their project.

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

    # 2️⃣ Wait for user response
    # This assumes you have a queue or context object where the WebSocket
    # endpoint puts user responses, e.g., ctx.deps.user_reply_queue
    user_clarification = await ctx.deps.user_reply_queue.get()

    # # 3️⃣ Fill the prompt template
    # filled_user_prompt = OVERVIEW_REFINEMENT_USER_PROMPT.format(
    #     overview=ctx.deps.task_specs_processed.overview,
    #     question_for_user=question_for_user,
    #     user_clarification=user_clarification
    # )

    # # 4️⃣ Refine with LLM
    # refined_overview = await refine_text_with_llm(
    #     model_choice=os.getenv("FEASIBILITY_CHECK_SUBTASK_LLM_CHOICE"),
    #     system_prompt=OVERVIEW_REFINEMENT_SYSTEM_PROMPT,
    #     user_prompt=filled_user_prompt,
    #     send_func=ctx.deps.send_func
    # )

    # # 5️⃣ Update context
    # ctx.deps.task_specs_processed.overview = refined_overview

    # Return the user clarification for the agent flow
    return user_clarification 