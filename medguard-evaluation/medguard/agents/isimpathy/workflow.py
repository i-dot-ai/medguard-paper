from inspect_ai.agent import Agent, AgentState, agent, run
from inspect_ai.model import ChatMessageAssistant

from medguard.agents.utils import agent_no_tools, agent_tool_calling_loop

from .aim_agent import AIM_PROMPT
from .decision_maker_agent import DECISION_MAKER_PROMPT
from .effectiveness_agent import EFFECTIVENESS_PROMPT, effectiveness_agent_tools
from .need_essential_agent import NEED_ESSENTIAL_PROMPT
from .need_unnecessary_agent import (
    NEED_UNNECESSARY_PROMPT,
    need_unnecessary_agent_tools,
)
from .patient_centred_agent import PATIENT_CENTRED_PROMPT, patient_centred_agent_tools
from .safety_agent import SAFETY_PROMPT, safety_agent_tools
from .sustainability_agent import SUSTAINABILITY_PROMPT, sustainability_agent_tools


@agent
def isimpathy_flagging() -> Agent:
    aim_agent = agent_no_tools(AIM_PROMPT)
    need_essential_agent = agent_no_tools(NEED_ESSENTIAL_PROMPT)
    need_unnecessary_agent = agent_tool_calling_loop(
        NEED_UNNECESSARY_PROMPT, need_unnecessary_agent_tools
    )
    effectiveness_agent = agent_tool_calling_loop(EFFECTIVENESS_PROMPT, effectiveness_agent_tools)
    safety_agent = agent_tool_calling_loop(SAFETY_PROMPT, safety_agent_tools)
    sustainability_agent = agent_tool_calling_loop(
        SUSTAINABILITY_PROMPT, sustainability_agent_tools
    )
    patient_centred_agent = agent_tool_calling_loop(
        PATIENT_CENTRED_PROMPT, patient_centred_agent_tools
    )
    decision_maker_agent = agent_no_tools(DECISION_MAKER_PROMPT)

    async def execute(state: AgentState) -> AgentState:
        state_aim = await run(aim_agent, state)
        state_need_essential = await run(need_essential_agent, state_aim)
        state_need_unnecessary = await run(need_unnecessary_agent, state_need_essential)
        state_effectiveness = await run(effectiveness_agent, state_need_unnecessary)
        state_safety = await run(safety_agent, state_effectiveness)
        state_sustainability = await run(sustainability_agent, state_safety)
        state_patient_centred = await run(patient_centred_agent, state_sustainability)

        state.messages.extend(
            [
                ChatMessageAssistant(
                    content="Aim Agent Output:\n" + state_aim.output.message.content
                ),
                ChatMessageAssistant(
                    content="Need Essential Agent Output:\n"
                    + state_need_essential.output.message.content
                ),
                ChatMessageAssistant(
                    content="Need Unnecessary Agent Output:\n"
                    + state_need_unnecessary.output.message.content
                ),
                ChatMessageAssistant(
                    content="Effectiveness Agent Output:\n"
                    + state_effectiveness.output.message.content
                ),
                ChatMessageAssistant(
                    content="Safety Agent Output:\n" + state_safety.output.message.content
                ),
                ChatMessageAssistant(
                    content="Sustainability Agent Output:\n"
                    + state_sustainability.output.message.content
                ),
                ChatMessageAssistant(
                    content="Patient Centred Agent Output:\n"
                    + state_patient_centred.output.message.content
                ),
            ]
        )

        state = await run(decision_maker_agent, state)

        return state

    return execute
