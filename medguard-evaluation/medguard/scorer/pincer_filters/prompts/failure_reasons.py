FAILURE_REASONS = """
1. Hallucination: MedGuard fabricated or invented information that does not exist in the patient record.
2. Input Processing Error: MedGuard misread, misextracted, or misinterpreted information that is present in the record.
3. Knowledge Gap: MedGuard lacks essential clinical knowledge required to assess the case correctly.
4. Reasoning Error: MedGuard has correct facts but applies flawed clinical logic or makes inappropriate inferences.
5. Quantitative Error: MedGuard makes mathematical, dosing, or criteria-counting errors.
6. Safety Critical Omission: MedGuard failed to address a serious safety concern that could lead to significant patient harm.
7. Non Critical Omission: MedGuard missed an opportunity for optimization but not addressing it won't cause immediate serious harm.
8. Guideline Non Adherence: MedGuard's intervention violates established clinical guidelines or safety protocols.
9. Confidence Calibration Error: MedGuard is overconfident about wrong priorities or inappropriately certain about uncertain situations.
"""

INCORRECT_GROUND_TRUTH_FAILURE_REASON = """
10. Incorrect Ground Truth: There is a very strong reason to believe there was an issue that needed to be addressed that the clinician correctly identified.
"""

FAILURE_ANALYSIS_OUTPUT_FORMAT = """
You must respond with valid JSON matching this exact schema:

{{
  "failure_analysis": [
    {{
      "reasoning": "string - detailed explanation with specific evidence",
      "reason": "string - one of: hallucination, knowledge_gap, safety_critical_omission, non_critical_omission, input_processing_error, reasoning_error, quantitative_error, confidence_calibration_error, guideline_non_adherence"
    }}
  ]
}}

Do not include any text outside the JSON object. Do not wrap the JSON in markdown code blocks.

---

## failure_analysis

Array of failure analysis objects. Include ALL applicable failure reasons.

**reasoning**: Detailed explanation with specific evidence from the patient profile and clinician's analysis. Quote what was missed, misread, or incorrectly prioritized.

**reason**: Must be one of: "hallucination", "knowledge_gap", "safety_critical_omission", "non_critical_omission", "input_processing_error", "reasoning_error", "quantitative_error", "confidence_calibration_error", "guideline_non_adherence".

Respond with valid JSON only. No additional text or formatting.
"""

FAILURE_ANALYSIS_OUTPUT_FORMAT_INCORRECT_GROUND_TRUTH = """
You must respond with valid JSON matching this exact schema:

{{
  "failure_analysis": [
    {{
      "reasoning": "string - detailed explanation with specific evidence",
      "reason": "string - one of: hallucination, knowledge_gap, safety_critical_omission, non_critical_omission, input_processing_error, reasoning_error, quantitative_error, confidence_calibration_error, guideline_non_adherence, incorrect_ground_truth"
    }}
  ]
}}

Do not include any text outside the JSON object. Do not wrap the JSON in markdown code blocks.

---

## failure_analysis

Array of failure analysis objects. Include ALL applicable failure reasons.

**reasoning**: Detailed explanation with specific evidence from the patient profile and clinician's analysis. Quote what was missed, misread, or incorrectly prioritized.

**reason**: Must be one of: "hallucination", "knowledge_gap", "safety_critical_omission", "non_critical_omission", "input_processing_error", "reasoning_error", "quantitative_error", "confidence_calibration_error", "guideline_non_adherence", "incorrect_ground_truth".

Respond with valid JSON only. No additional text or formatting.
"""
