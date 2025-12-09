from inspect_ai import Task, task
from inspect_ai.dataset import json_dataset

from medguard.agents.reasoning_agent.workflow import reasoning_agent
from medguard.ground_truth.utils import record_to_sample
from medguard.scorer.ground_truth.scorer import llm_as_a_judge

dataset = json_dataset(
    "inputs/2025-10-31-patient-profiles-ground-truth-190.jsonl",
    record_to_sample,
)


@task
def eval_reasoning():
    return Task(dataset=dataset, solver=[reasoning_agent()], scorer=llm_as_a_judge())
