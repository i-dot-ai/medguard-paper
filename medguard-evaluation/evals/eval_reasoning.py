from inspect_ai import Task, task
from inspect_ai.dataset import json_dataset

from medguard.agents.reasoning_agent.workflow import reasoning_agent
from medguard.data_ingest.record_to_sample import record_to_sample
from medguard.scorer.pincer_filters.scorer import llm_as_a_judge

dataset = json_dataset(
    "inputs/2025-10-27-patient-profiles-no-filter_n3999.jsonl",
    record_to_sample,
)


@task
def eval_reasoning():
    return Task(dataset=dataset, solver=[reasoning_agent()], scorer=llm_as_a_judge())
