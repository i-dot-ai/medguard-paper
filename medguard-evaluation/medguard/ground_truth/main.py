import asyncio
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from medguard.evaluation.clinician.models import Stage2Data
from medguard.evaluation.clinician.utils import load_evaluations_from_folder
from medguard.evaluation.themefinder import OpenAISemaphoreClient
from medguard.evaluation.utils import load_analysed_patient_records_from_jsonl
from medguard.ground_truth.examples import examples, format_examples
from medguard.ground_truth.models import GroundTruthAssessment, GroundTruthAssessmentFull
from medguard.scorer.models import MedGuardAnalysis
from medguard.utils.parsing import save_pydantic_list_to_jsonl

PROMPT = f"""
You are an expert at creating a ground truth intervention recommendation for a patient given initial recommendations and subsequentfeedback from a clinician. 

You are given a list of issues and a proposed intervention along with feedback from an expert clinician.

You should update the issues and intervention to accurately reflect the clinician's feedback.

Rules:
- Where possible, keep the original wording of the issues and intervention from the initial recommendation or clinician feedback.
- Update the issues and intervention where the clinician's feedback suggests as much.
- Do not include in the answer any issues or interventions that haven't been mentioned in your input.
- If the clinician agrees with an intervention, but the initial assessment said it didn't require an intervention, then this issue should be recorded as a note in the updated intervention.
- For the updated intervention, consider the clinician's feedback on the original intervention and which parts of it are still necessary. If required, consider their feedback on the original issues as well to inform the intervention.

The following should not be included in the ground truth intervention:
- Generic recommendations unless explicitly confirmed by the clinician (to keep generic recommendations, it is not enough for the clinician to agree with the intervention as a whole, they must explicitly state these recommendations as necessary in their feedback).


The following should not be included in the ground truth interventions unless explicitly stated by the clinician. You should use your judgement to exclude similar generic recommendations.
- Conditional recommendations (if X continues, consider Y; do X if Y happens) should not be included in the interventions.
- Arrange a fall‑risk assessment and physiotherapy review following medication changes.
- Document all changes and communicate with the multidisciplinary team and the patient’s carer.
- Document the decision and arrange cardiology input if the patient is under specialist care.
- Arrange a review with the prescriber to plan a taper schedule and consider alternative anxiety/sleep management strategies.
- Arrange review of lower urinary tract symptoms, including a detailed urological history and assessment of finasteride therapy.
- Arrange shared decision‑making regarding continuation or deprescribing of the statin.
- Document the outcome of the above discussions and any subsequent plan (e.g., continue propranolol, no statin prescribed).
This means that even if they're included in an intervention that the clinician agrees with, you should still remove them from the ground truth intervention.
Instead, you should document these in the notes.

For example:
- "Discontinue aspirin 75 mg daily and document that bleeding risk outweighs secondary CHD benefit while the patient is on therapeutic apixaban for recent pulmonary embolism." might be included in an intervention the clinician agrees with. Even if that is the case you would only record "Discontinue aspirin 75 mg daily" in your intervention.

Output format:
- reasoning: A concise summary of the changes made to the initial assessment based on clinician feedback
- issues: List of validated clinical issues
- intervention: The updated intervention recommendation (or null if none needed)
- notes: Additional contextual information that doesn't require intervention

Here are some examples:
{format_examples(examples)}

As a reminder, note how the ground truth assessment should be based only on the clinician's feedback. You should not add any wording, or extent anything based on your own knowledge. 

ONLY include in the ground truth things that you have evidence for from the initial review or clinician's feedback.
"""


class Output(BaseModel):
    patient_id: str
    stage2: Stage2Data
    medguard_analysis: MedGuardAnalysis


def output_to_prompt(output: Output) -> str:
    """Convert an Output object to a prompt string for the LLM."""
    prompt = ""

    # Initial issues identified by MedGuard, along with feedback from Lauren
    # Ensure we only iterate over the minimum length to avoid index errors
    num_issues = min(
        len(output.stage2.issue_assessments),
        len(output.stage2.issue_reasoning),
        len(output.medguard_analysis.clinical_issues),
    )

    for i in range(num_issues):
        issue_assessment = output.stage2.issue_assessments[i]
        issue_reasoning = output.stage2.issue_reasoning[i]
        issue = output.medguard_analysis.clinical_issues[i]

        prompt += f"\n**Issue {i + 1}**\n"
        prompt += f"issue: {issue.issue}\n"
        prompt += f"evidence: {issue.evidence}\n"
        prompt += f"intervention required: {issue.intervention_required}\n\n"

        prompt += f"clinician agrees with issue: {issue_assessment}\n"
        if issue_reasoning:
            prompt += f"clinician reasoning: {issue_reasoning}\n"

    # If necessary, include details of missed issues
    if output.stage2.missed_issues == "yes" and output.stage2.missed_issues_detail:
        prompt += f"\nThe initial assessment also missed the following issues: {output.stage2.missed_issues_detail}\n"

    prompt += "\n**Intervention**\n"
    prompt += f"intervention required: {output.medguard_analysis.intervention_required}\n"
    prompt += f"intervention: {output.medguard_analysis.intervention}\n"

    prompt += (
        f"clinician agrees with the intervention: {output.stage2.medguard_specific_intervention}\n"
    )

    if output.stage2.medguard_specific_intervention_reasoning:
        prompt += f"clinician reasoning: {output.stage2.medguard_specific_intervention_reasoning}\n"
    if output.stage2.intervention_should_be:
        prompt += f"intervention should be: {output.stage2.intervention_should_be}\n"

    return prompt


async def generate_ground_truth(
    test_set_path: str,
    evaluation_folder_path: str,
    output_path: str,
    model: str = "openai/gpt-oss-120b",
    max_concurrent_requests: int = 15,
):
    """
    Generate ground truth assessments from MedGuard analyses and clinician evaluations.

    Args:
        test_set_path: Path to the test set patient records JSONL file
        evaluation_folder_path: Path to folder containing evaluation JSON files
        output_path: Path where to save the ground truth assessments JSONL file
        model: Model to use for generation
        max_concurrent_requests: Maximum number of concurrent API requests
    """
    print(f"Loading evaluations from {evaluation_folder_path}...")
    evaluations = load_evaluations_from_folder(evaluation_folder_path)

    print(f"Loading analyses from {test_set_path}...")
    analyses = load_analysed_patient_records_from_jsonl(test_set_path)

    # Filter to only evaluations with stage2 data
    evaluations = [x for x in evaluations if x.stage2]
    print(f"Found {len(evaluations)} evaluations with stage2 data")

    # Create dictionary for fast lookup
    analyses_dict = {x.patient_link_id: x for x in analyses}

    # Create Output objects combining evaluations and analyses
    outputs: list[Output] = []
    for evaluation in evaluations:
        medguard_analysis = analyses_dict[int(evaluation.patient_id)].medguard_analysis
        outputs.append(
            Output(
                patient_id=str(evaluation.patient_id),
                stage2=evaluation.stage2,
                medguard_analysis=medguard_analysis,
            )
        )

    print(f"Created {len(outputs)} output objects to process")

    # Prepare all messages for batch processing
    print("Preparing messages for batch processing...")
    messages_list = []
    for output in outputs:
        messages = [
            {"role": "system", "content": PROMPT},
            {
                "role": "user",
                "content": "Please update the intervention for the following example:\n"
                + output_to_prompt(output),
            },
        ]
        messages_list.append(messages)

    # Run batch async requests
    print(
        f"Processing {len(messages_list)} requests with {max_concurrent_requests} concurrent requests..."
    )
    async with OpenAISemaphoreClient(max_concurrent_requests=max_concurrent_requests) as client:
        ground_truth_results = await client.batch_parse_completions(
            model=model,
            messages_list=messages_list,
            response_format=GroundTruthAssessment,
            return_full_response=True,
        )

    # Convert to GroundTruthAssessmentFull by adding patient_id, assessment_date, and internal_reasoning
    print("\nConverting to GroundTruthAssessmentFull...")
    ground_truth_full: list[GroundTruthAssessmentFull] = []

    for output, result in zip(outputs, ground_truth_results):
        if not isinstance(result, Exception):
            # Extract internal reasoning from the raw text output
            internal_reasoning = result.output[0].content[0].text

            # Get the parsed output
            parsed = result.output_parsed

            # Create GroundTruthAssessmentFull with patient metadata
            full_assessment = GroundTruthAssessmentFull(
                internal_reasoning=internal_reasoning,
                reasoning=parsed.reasoning,
                issues=parsed.issues,
                intervention=parsed.intervention,
                notes=parsed.notes,
                patient_id=output.patient_id,
                assessment_date=datetime.now(),
            )
            ground_truth_full.append(full_assessment)

    print(f"Created {len(ground_truth_full)} GroundTruthAssessmentFull objects")

    # Save to JSONL
    print(f"\nSaving to {output_path}...")
    save_pydantic_list_to_jsonl(ground_truth_full, output_path)
    print(f"✓ Saved {len(ground_truth_full)} ground truth assessments")


def main():
    """Main entry point for ground truth generation."""
    # Configuration
    test_set_path = "outputs/20251018/test-set/patient_records.jsonl"
    evaluation_folder_path = "outputs/evaluations/evaluations_test"

    # Create output directory if it doesn't exist
    output_dir = Path("outputs/ground_truth")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Output file with date
    output_path = output_dir / "2025-10-28-test-set-new.jsonl"

    # Run async generation
    asyncio.run(
        generate_ground_truth(
            test_set_path=test_set_path,
            evaluation_folder_path=evaluation_folder_path,
            output_path=str(output_path),
        )
    )


if __name__ == "__main__":
    main()
