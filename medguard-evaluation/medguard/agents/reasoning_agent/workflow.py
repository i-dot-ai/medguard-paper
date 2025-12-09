from inspect_ai.agent import Agent, AgentState, agent
from inspect_ai.model import ChatMessageSystem, GenerateConfig, ResponseSchema, get_model
from inspect_ai.util import json_schema

from medguard.scorer.models import MedGuardAnalysis

from .prompt import REASONING_PROMPT


@agent
def reasoning_agent() -> Agent:
    async def execute(state: AgentState) -> AgentState:
        state.messages = [ChatMessageSystem(content=REASONING_PROMPT)] + state.messages

        config = GenerateConfig(
            response_schema=ResponseSchema(
                name="MedGuardAnalysis", json_schema=json_schema(MedGuardAnalysis)
            )
        )

        state.output = await get_model().generate(input=state.messages, config=config)

        state.messages.append(state.output.message)

        return state

    return execute
