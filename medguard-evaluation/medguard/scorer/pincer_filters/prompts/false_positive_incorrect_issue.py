from medguard.scorer.pincer_filters.prompts.failure_mode_examples import FAILURE_MODE_EXAMPLES
from .failure_reasons import FAILURE_ANALYSIS_OUTPUT_FORMAT_INCORRECT_GROUND_TRUTH, FAILURE_REASONS

FALSE_POSITIVE_INCORRECT_ISSUE_PROMPT = (
    """
You are an expert at assessing the failure reasons for a clinician's assessment of a patient's medication profile.

You will be provided with the following information:
1. patient_profile: The patient the clinician was assessing
2. patient_analysis: The analysis from the clinician, including their medication review, interaction review, clinical issue review, intervention review, intervention required, and confidence
3. actual_issue: The actual issue that the patient was facing.

The clinician incorrectly identified the issue that the patient was facing.

Your job is to review their analysis and identify the reasons for their incorrect classification.

<patient_profile>
{patient_profile}
</patient_profile>

<patient_analysis>
{patient_analysis}
</patient_analysis>

<flagged_clinical_issue>
{flagged_clinical_issue}
</flagged_clinical_issue>

<failure_reasons>
"""
    + FAILURE_REASONS
    + """
</failure_reasons>

<examples>
"""
    + FAILURE_MODE_EXAMPLES
    + """
</examples>

As a reminder, your task is to identify where the clinician's reasoning went wrong. You should only use your medical knowledge to assess their medical reasoning, and not to try and diagnose the patient yourself.

Where the clinician has identified the presence of an issue but not the correct issue, it's possible that the clinician has hinted at the correct issue but not explicity stated it. In this case you should include partial identification as a failure reason.

Each distinct error should be assigned to only ONE failure reason category. However, if there are multiple independent errors in the analysis, you can identify multiple failure reasons (one per error).

For example:
- ✓ Correct: Missing a critical lab value (facts) AND flawed clinical logic in dosing decision (reasoning) = 2 failure reasons
- ✗ Incorrect: Missing a critical lab value categorized as both "facts" AND "safety" = don't double-count the same error

---

"""
    + FAILURE_ANALYSIS_OUTPUT_FORMAT_INCORRECT_GROUND_TRUTH
)
