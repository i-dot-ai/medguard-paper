from medguard.scorer.pincer_filters.prompts.failure_mode_examples import FAILURE_MODE_EXAMPLES
from .failure_reasons import (
    FAILURE_ANALYSIS_OUTPUT_FORMAT_INCORRECT_GROUND_TRUTH,
    FAILURE_REASONS,
    INCORRECT_GROUND_TRUTH_FAILURE_REASON,
)

FALSE_POSITIVE_PROMPT = (
    """
You are an expert at assessing the failure reasons for a clinician's assessment of a patient's medication profile.

You will be provided with the following information:
1. patient_profile: The patient the clinician was assessing
2. patient_analysis: The analysis from the clinician, including their medication review, interaction review, clinical issue review, intervention review, intervention required, and confidence

The clinician identified that there was a required intervention for this patient, whereas the ground truth suggested that the patient did not have an issue that needed to be addressed.

Your job is to review their analysis and identify the correct failure reasons.

<patient_profile>
{patient_profile}
</patient_profile>

<patient_analysis>
{patient_analysis}
</patient_analysis>

<failure_reasons>
"""
    + FAILURE_REASONS
    + INCORRECT_GROUND_TRUTH_FAILURE_REASON
    + """
</failure_reasons>

<examples>
"""
    + FAILURE_MODE_EXAMPLES
    + """
</examples>

## Step 1: Confirm the ground truth is correct

It's highly likely that the patient did not have an issue that needed to be addressed, and that the clinician was mistaken in their assessment. Nevertheless if you have INCREDIBLY HIGH CONFIDENCE that there was an issue that needed to be addressed which the clinician correctly identified then you should include the Incorrect Ground Truth failure reason

However, if as expected you have ruled out the unlikely possibility that the ground truth is mistaken or there are nevertheless issues with the analysis, you should identify the failure reasons that apply to the clinician's assessment.

## Step 2: Identify the failure reasons

Identify all the failure reasons that apply to the clinician's assessment.

Each distinct error should be assigned to only ONE failure reason category. However, if there are multiple independent errors in the analysis, you can identify multiple failure reasons (one per error).

For example:
- ✓ Correct: Missing a critical lab value (facts) AND flawed clinical logic in dosing decision (reasoning) = 2 failure reasons
- ✗ Incorrect: Missing a critical lab value categorized as both "facts" AND "safety" = don't double-count the same error

In your reasoning you should explain in detail each failure reason and why it applies to the clinician's assessment.

Please provide the failure reasons for the above patient analysis.

---

"""
    + FAILURE_ANALYSIS_OUTPUT_FORMAT_INCORRECT_GROUND_TRUTH
)
