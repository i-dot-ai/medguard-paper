CRITIQUE_COMPLETION_TEMPLATE = """
Given the following review instructions, clinician's review and areas for improvement please generate an improved review:

<clinicians_original_instructions>
{clinician_instructions}
</clinicians_original_instructions>

<patient_history>
{patient_history}
</patient_history>

<clinician_initial_review>
{clinician_initial_review}
</clinician_initial_review>

<areas_for_improvement>
{areas_for_improvement}
</areas_for_improvement>

Remember, you should not introduce new medical thinking at this stage. You should only update the existing review with one of the following actions:
1. Keep the existing review unchanged.
2. For a given clinical issue, remove it based on the guidance provided by the areas for improvement.
3. For a given clinical issue, update it from intervention_required=true to intervention_required=false based on the guidance provided by the areas for improvement.
4. As a result of changes above, update the subsequent fields in the JSON object accordingly.

For an analysis that does not currently require an intervention, under no circumstances should you update the recommendation to require an intervention.

As per the original clinician, your improved review must respond with valid JSON matching this exact schema:

{{
  "patient_review": "string - comprehensive synthesis",
  "clinical_issues": [
    {{
      "issue": "string - brief description",
      "evidence": "string - specific evidence with dates/values",
      "intervention_required": boolean
    }}
  ],
  "intervention": "string - action plan or empty string if none needed",
  "intervention_required": boolean
  "intervention_probability": float between 0 and 1,
}}

Do not include any text outside the JSON object. Do not wrap the JSON in markdown code blocks.
"""
