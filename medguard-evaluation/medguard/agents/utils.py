from inspect_ai.agent import Agent, AgentState, agent
from inspect_ai.model import ChatMessageSystem, get_model, execute_tools
from inspect_ai.tool import Tool


@agent
def agent_no_tools(prompt: str) -> Agent:
    async def execute(state: AgentState) -> AgentState:
        state.messages.append(ChatMessageSystem(content=prompt))

        state.output = await get_model().generate(input=state.messages)

        state.messages.append(state.output.message)

        return state

    return execute


@agent
def agent_tool_calling_loop(prompt: str, tools: list[Tool]) -> Agent:
    async def execute(state: AgentState) -> AgentState:
        state.messages.append(ChatMessageSystem(content=prompt))

        messages, state.output = await get_model().generate_loop(state.messages, tools=tools)
        state.messages.extend(messages)
        return state

    return execute


@agent
def agent_tool_calling_single_loop(prompt: str, tools: list[Tool]) -> Agent:
    async def execute(state: AgentState) -> AgentState:
        state.messages.append(ChatMessageSystem(content=prompt))

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
