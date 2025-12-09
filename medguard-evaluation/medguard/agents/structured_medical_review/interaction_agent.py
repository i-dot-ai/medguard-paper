from inspect_ai.agent import Agent, AgentState, agent
from inspect_ai.model import ChatMessageSystem, execute_tools, get_model

from medguard.tools import (
    get_bnf_drug_interactions,
)

INTERACTIONS_PROMPT = r"""
# Task:
You are an expert AI assistant in the UK helping a pharmacist review a patients prescription profile.
Your job is to use the available tools to retrieve extra information to better inform the pharmacist with evidence-based information.

# Rules:
* Always use the tools to provide information.
* If no tool is needed to answer the question, use the ignore tool to forward the message to the specialist.
* Never respond directly to the user.
"""


@agent
def interaction_flagger() -> Agent:
    tools = [
        get_bnf_drug_interactions(),
    ]

    async def execute(state: AgentState) -> AgentState:
        state.messages.append(ChatMessageSystem(content=INTERACTIONS_PROMPT))

        # This calls the model, but we must then execute any tool calls
        output = await get_model().generate(
            input=state.messages,
            tools=tools,
        )

        state.messages.append(output.message)

        # If the model calls a tool, we must execute the tool
        if output.message.tool_calls:
            tools_messages, tools_output = await execute_tools(state.messages, tools)
            state.messages.extend(tools_messages)
            if tools_output is not None:
                output = tools_output

        return state

    return execute
