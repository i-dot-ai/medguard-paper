from uuid import uuid4

from inspect_ai.dataset import Sample

from medguard.data_ingest.record_to_sample import load_profile_json_to_pydantic
from medguard.utils.parsing import read_jsonl

from .models import GroundTruthAssessment, GroundTruthAssessmentFull


def load_ground_truth_samples(
    path: str = "outputs/ground_truth/2025-10-28-test-set.jsonl",
) -> dict[str, GroundTruthAssessmentFull]:
    # Load the ground truth samples
    ground_truth_samples = [
        GroundTruthAssessmentFull.model_validate(sample) for sample in read_jsonl(path)
    ]
    ground_truth_samples_dict = {int(sample.patient_id): sample for sample in ground_truth_samples}
    return ground_truth_samples_dict


def record_to_sample(record: dict) -> Sample:
    patient = load_profile_json_to_pydantic(record)

    prompt, review_date = patient.get_prompt_and_date()

    ground_truth = load_ground_truth_samples()[patient.patient_link_id]

    return Sample(
        input=prompt,
        target=GroundTruthAssessment.model_validate(ground_truth.model_dump()).model_dump_json(
            indent=2
        ),
        id=str(uuid4()),
        metadata={
            "patient_id": patient.patient_link_id,
            "review_date": review_date,
            "ground_truth": GroundTruthAssessment.model_validate(
                ground_truth.model_dump()
            ).model_dump(),
        },
    )
