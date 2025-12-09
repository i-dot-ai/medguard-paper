from medguard.scorer.pincer_filters.prompts.intervention_classification_examples import (
    INTERVENTION_CLASSIFICATION_EXAMPLES,
)


INTERVENTION_CLASSIFICATION_PROMPT = (
    """
You are an expert at assessing whether a proposed intervention will correctly address a patient's needs.

You will be provided with an intervention from a clinician, and the flagged issue which the intervention must address. Your job is to assess whether the intervention correctly addresses the flagged issue.

In assessing the intervention, you must consider whether the intervention will lead to any of the above factors no longer being true.

For example, if the factors were:
1. Have a recorded diagnosis of peptic ulcer OR gastrointestinal hemorrhage
2. Have been prescribed aspirin or clopidogrel after their diagnosis
3. Do NOT have a co-prescribed proton pump inhibitor (PPI) during the antiplatelet prescription

Then an intervention must address at least one of these factors.

Here are some examples of interventions that would address the factors:
1. Prescribe a PPI to the patient
2. Stop the patient's aspirin or clopidogrel
3. Change the patient's aspirin or clopidogrel to a different medication

Here are some examples of interventions that would not address the factors:
1. Alters the patient's aspirin dose to a lower dose. (although this may reduce the aspirin prescription, the patient still has an aspirin prescription and therefore would still satisfy all the factors)
2. Changes the patient's PPI to a different PPI. (although this may change the PPI prescription, the patient still has a PPI prescription and therefore would still satisfy all the factors)
3. Prescribes a new medication to the patient that is unrelated to any of the factors. (although this has changed the medication profile, the patient still satisfies all the factors)

If the intervention will result in one or more of the factors no longer being true, then the intervention is correct and you should mark the intervention as correct.

If the intervention will not result in one or more of the factors no longer being true, then the intervention is incorrect and you should mark the intervention as incorrect.

<examples>
"""
    + INTERVENTION_CLASSIFICATION_EXAMPLES
    + """
</examples>

You will now review the following case:

Flagged Clinical Issue: {clinical_issue}

MedGuard Patient Summary: {patient_summary}

MedGuard Identified the following issues: {medguard_issues}

These were then reviewed by a clinician to assess their correctness:
{issue_reasoning}

MedGuard believed an intervention was required.

MedGuard's intervention: {intervention}

Please consider whether the intervention is appropriate for the patient and provide your reasoning.

You must respond with valid JSON matching this exact schema:

{{
  "reasoning": "string - detailed explanation with specific evidence",
  "correct": bool
}}

Do not include any text outside the JSON object. Do not wrap the JSON in markdown code blocks.
"""
)
