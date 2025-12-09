from inspect_ai.agent import Agent, AgentState, agent, run
from inspect_ai.model import ChatMessageUser

from .smr_agent import smr_agent
from .interaction_agent import interaction_flagger
from .flagging_agent import patient_flagger


@agent
def structured_medical_review() -> Agent:
    async def execute(state: AgentState) -> AgentState:
        state = await run(smr_agent(), state)

        state.messages.append(
            ChatMessageUser(content="Are there any interactions between the patients drugs?")
        )
        state = await run(interaction_flagger(), state)
        state = await run(patient_flagger(), state)

        return state

    return execute
