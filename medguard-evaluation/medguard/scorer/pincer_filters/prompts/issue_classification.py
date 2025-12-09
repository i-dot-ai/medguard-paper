# this prompt is used to classify the clinical issue identified by the clinician into one of the Enum values
from medguard.scorer.pincer_filters.prompts.intervention_classification_examples import (
    INTERVENTION_CLASSIFICATION_EXAMPLES,
)


CLINICAL_ISSUE_CLASSIFICATION_PROMPT = (
    """
You are an expert at assessing whether MedGuard has correctly identified a flagged clinical issue.

You will be provided with:
1. A series of clinical issues identified by MedGuard
2. The flagged clinical issue that you will assess MedGuard against

Your task is to either:
- Indicate that MedGuard has correctly identified the flagged clinical issue
- Indicate that MedGuard has not correctly identified the flagged clinical issue

Here are some examples taken from another clinician considering this:

<examples>
"""
    + INTERVENTION_CLASSIFICATION_EXAMPLES
    + """
</examples>

As in the examples, you will need to output the following fields:
reasoning: str - This should be an explanation of your reasoning for why you chose the category you did.
issue_correct: boolean - This should be true if MedGuard has correctly identified the flagged clinical issue, false otherwise.

You will now review the following case:

Flagged Clinical Issue: {clinical_issue}

MedGuard Patient Summary: {patient_summary}

MedGuard Identified the following issues: {medguard_issues}

Please assess whether MedGuard has correctly identified the flagged clinical issue and provide your reasoning.
"""
)
