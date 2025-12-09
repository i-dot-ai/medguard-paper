CRITIQUE_TEMPLATE = """
You are tasked with providing constructive critique to another expert clinician's review of a patient's medication profile. This feedback will be used by the clinician to improve their review. You are unlikely to find issues with the clinician's review, this is an additional layer of safety/a spot check.

<clinicians_original_instructions>
{clinician_instructions}
</clinicians_original_instructions>

<patient_history>
{patient_history}
</patient_history>

<clinician_review>
{clinician_review}
</clinician_review>

<areas_for_improvement>
One of your main contributions should be identifying False Positive cases as currently this system is leading to alert fatigue. Common issues which lead to FPs include but are not limited to the following:

**Clinical Facts Completeness:** Have ALL relevant clinical events been considered?
**Temporal Context:** Is the issue current and active, or historical/resolved?
**Dosing and Administration:** Correct dosage calculation?  Overly sensitive to duplicative prescriptions - a common best practice to achieve desired dosage?
**Patient-Specific Context:** Is this palliative/end-of-life care or does the patient's context mean benefits of current management outweigh theoretical risks?
**Clinical Significance vs. Guideline Compliance:** Are you being overly cautious about patterns that are clinically acceptable?
</areas_for_improvement>
"""
