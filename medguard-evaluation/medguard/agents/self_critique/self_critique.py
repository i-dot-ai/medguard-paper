from inspect_ai._util.dict import omit
from inspect_ai.agent import Agent, AgentState, agent
from inspect_ai.model import (
    ChatMessageSystem,
    ChatMessageUser,
    GenerateConfig,
    Model,
    ResponseSchema,
    get_model,
)
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import json_schema, resource

from medguard.agents.reasoning_agent.prompts.current_prompt import REASONING_PROMPT
from medguard.scorer.models import MedGuardAnalysis
from medguard.scorer.prompts.failure_reasons import FAILURE_REASONS

from .completion_template import CRITIQUE_COMPLETION_TEMPLATE
from .critique_template import CRITIQUE_TEMPLATE


@solver
def self_critique(
    critique_template: str | None = CRITIQUE_TEMPLATE,
    completion_template: str | None = CRITIQUE_COMPLETION_TEMPLATE,
    clinician_instructions: str | None = REASONING_PROMPT,
    failure_reasons: str | None = FAILURE_REASONS,
    model: str | Model | None = None,
) -> Solver:
    # resolve templates

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        # resolve model
        nonlocal model
        model = model if isinstance(model, Model) else get_model(model)

        # run critique
        critique_system_prompt = "You are doctor specialising in clinical pharmacology providing constructive critique to help improve the quality of medication reviews and reduce False Postive rates."

        critique_messages = [
            ChatMessageSystem(content=critique_system_prompt),
            ChatMessageUser(
                content=critique_template.format(
                    clinician_instructions=clinician_instructions,
                    patient_history=state.input_text,
                    clinician_review=state.output.completion,
                    areas_for_improvement=failure_reasons,
                )
            ),
        ]

        critique = await model.generate(critique_messages)

        # add the critique as a user message
        state.messages.append(
            ChatMessageUser(
                content=completion_template.format(
                    clinician_instructions=clinician_instructions,
                    patient_history=state.input_text,
                    clinician_initial_review=state.output.completion,
                    areas_for_improvement=critique.completion,
                ),
            )
        )

        config = GenerateConfig(
            response_schema=ResponseSchema(
                name="MedGuardAnalysis", json_schema=json_schema(MedGuardAnalysis)
            )
        )

        state.output = await model.generate(input=state.messages, config=config)

        state.messages.append(state.output.message)

        return state

    return solve
