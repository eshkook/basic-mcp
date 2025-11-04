import asyncio
import os

from .models import (
    LlmCallInput
)
from .tools import (
    refine_text_with_llm
)
from .prompts import (
    OVERVIEW_REFINEMENT_SYSTEM_PROMPT,
    OVERVIEW_REFINEMENT_USER_PROMPT
)

overview = '''

'''

question_for_user = '''

'''

user_clarification = '''

'''

async def main():

    filled_user_prompt = OVERVIEW_REFINEMENT_USER_PROMPT.format(
        overview=overview,
        question_for_user=question_for_user,
        user_clarification=user_clarification
    )

    data = LlmCallInput(prompt=filled_user_prompt)

    filled_user_prompt = data.prompt

    # 4️⃣ Refine with LLM
    refined_overview = await refine_text_with_llm(
        model_choice=os.getenv('LLM_MODEL'),
        system_prompt=OVERVIEW_REFINEMENT_SYSTEM_PROMPT,
        user_prompt=filled_user_prompt
        # send_func=ctx.deps.send_func # uncomment when need to stream tokens to client
    )

    print(refined_overview)

if __name__ == "__main__":
    asyncio.run(main())