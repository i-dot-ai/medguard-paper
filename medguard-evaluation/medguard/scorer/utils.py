import json
from typing import Type, TypeVar

from inspect_ai.model import GenerateConfig, Model, ResponseSchema
from inspect_ai.util import json_schema
from pydantic import BaseModel, ValidationError

from inspect_ai.solver import TaskState
from medguard.scorer.models import MedGuardAnalysis
from inspect_ai.model import get_model

import logging

logger = logging.getLogger(__name__)


T = TypeVar("T", bound=BaseModel)


async def get_structured_output(model: Model, prompt: str, response_schema: Type[T]) -> T:
    model = get_model("vllm/openai/gpt-oss-120b")

    print("Calling structured output for type: ", response_schema.__name__)

    # We need to set the reasoning effort to medium to ensure that the scorers are consistent across different runs.
    # If we do not do this, then the scorer will use the reasoning effort from the base config. This would mean that we're using different reasoning efforts for scoring different runs, which is obviously bad.
    config = GenerateConfig(
        response_schema=ResponseSchema(
            name="clinical_issue", json_schema=json_schema(response_schema)
        ),
        reasoning_effort="medium",
        max_connections=30,
    )

    max_retries = 5
    for attempt in range(max_retries):
        try:
            res = await model.generate(prompt, config=config)
            return response_schema.model_validate(
                json.loads(res.choices[0].message.content[-1].text)
            )
        except (ValidationError, json.JSONDecodeError) as e:
            print(res.choices[0].message.content[-1].text)
            if attempt < max_retries - 1:
                print(
                    f"Validation error on attempt {attempt + 1}/{max_retries} for {response_schema.__name__}: {e}"
                )
            else:
                print(
                    f"Validation failed after {max_retries} attempts for {response_schema.__name__}"
                )
                raise


def get_medguard_analysis_from_state(state: TaskState) -> MedGuardAnalysis:
    return MedGuardAnalysis.model_validate_json(state.output.completion)
