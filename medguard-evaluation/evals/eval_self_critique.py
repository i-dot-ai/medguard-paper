from inspect_ai import Task, task
from inspect_ai.dataset import json_dataset

from medguard.agents.reasoning_agent.workflow import reasoning_agent
from medguard.agents.self_critique.self_critique import self_critique
from medguard.data_ingest.record_to_sample import record_to_sample
from medguard.scorer.pincer_filters.scorer import llm_as_a_judge

dataset = json_dataset(
    "inputs/2025-10-17-patient-profiles-10-filters-n500-train.jsonl",
    record_to_sample,
)


@task
def eval_self_critique():
    return Task(
        dataset=dataset, solver=[reasoning_agent(), self_critique()], scorer=llm_as_a_judge()
    )
