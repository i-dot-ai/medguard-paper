INTERVENTION_CLASSIFICATION_PROMPT = """
You are an expert at assessing whether an intervention proposed by a clinician is also included in a ground truth agreed by a panel of experts, and which part of the ground truth it corresponds to.

You will be provided with an intervention proposed by a clinician and the ground truth agreed by a panel of experts.

Your task is to assess whether the interventions proposed by the clinician is contained in a ground truth agreed by a panel of experts, and to indicate if necessary which element from the ground truth it corresponds to.

Here are some rules:
- If the intervention is not in the ground truth, then the intervention is incorrect and it doesn't match.
- If the intervention from the clinician is not specific enough to refer to the same intervention as one in the ground truth, then the intervention is incorrect.
- If the intervention from the clinician is specific enough to refer to the same issue as one in the ground truth then it is correct. If it's borderline, generally give the benefit of the doubt to the clinician and mark the intervention as correct.
- You should only use your medical knowledge to resolve language differences, rather than anything more specific.

Here are some examples:

<examples>

<example>
    ground truth interventions: 
    1. Prescribe an inhaled corticosteroid (e.g., beclometasone 100 µg inhaler, 2 puffs twice daily) and arrange a focused asthma education session to improve adherence.
    2. Restart atorvastatin 40 mg once daily (or 20 mg if tolerance is a concern) for secondary prevention of CHD; monitor liver function and CKD parameters after 4‑6 weeks.
    3. Restart ramipril 2.5 mg once daily, titrating up as tolerated, to control blood pressure, provide renal protection, and reduce cardiovascular risk
    4. Re‑check serum creatinine and potassium in 2 weeks.

    clinician intervention: Restart low‑dose aspirin 75 mg once daily for secondary prevention of CHD, unless a contraindication (e.g., active bleed) is identified.

    reasoning: The clinician intervention is not included in the ground truth intervention, so we cannot mark it as having matched with anything.
    correct: false
    match_id: null
</example>

<example>
    ground truth interventions: 
    1. Order serum creatinine, urea and calculate eGFR/CrCl. If eGFR falls <30 mL/min/1.73 m² (or CrCl <30 mL/min), reduce apixaban to 2.5 mg twice daily per dose‑adjustment guidelines; otherwise continue current dose and repeat renal monitoring annually.

    clinician intervention: The doctor should order serum creatinine, urea and calculate eGFR/CrCl within the next two weeks.

    reasoning: The clinician intervention is included in the ground truth intervention. Although the ground truth includes specific wording around the next two weeks, it is still correct as it can be reasonably inferred from the clinician's intervention that the doctor should order them immediately.
    correct: true
    match_id: 1
</example>

<example>   
    ground truth interventions: 
    1. Discontinue the duplicate furosemide prescription and reduce the total daily dose to 80 mg (e.g., 40 mg twice daily) to avoid over‑diuresis. 
    2. Initiate an ACE inhibitor such as ramipril 2.5 mg once daily (titrating to target) to achieve blood pressure control and provide renal protection. 
    3. Reduce gabapentin to 300 mg three times daily (total 900 mg/day) and arrange a review of neuropathic pain control with monitoring for dizziness or falls.

    clinician intervention: Reduce gabapentin to 300 mg three times daily.

    reasoning: The ground truth intervention includes substantial detail around follow ups from the dose reduction that are a core part of the intervention. Because the clinician's intervention does not include these key details, it is incorrect and doesn't match any of the ground truth.
    correct: false
    match_id: null
</example>

<example>
    ground truth interventions: 
    1. Discontinue the duplicate furosemide prescription and reduce the total daily dose to 80 mg (e.g., 40 mg twice daily) to avoid over‑diuresis. 
    2. Initiate an ACE inhibitor such as ramipril 2.5 mg once daily (titrating to target) to achieve blood pressure control and provide renal protection. 
    3. Reduce the dose of gabapentin to 300 mg three times daily.

    clinician intervention: Reduce gabapentin to 300 mg three times daily (total 900 mg/day)

    reasoning: This is similar to the example directly above, but unlike it the ground truth now includes no reference to the follow up. Therefore the clinician's intervention is correct and matches intervention 3.
    correct: true
    match_id: 3
</example>

<example>
    ground truth interventions: 
    1. Stop atenolol 100 mg and reassess blood pressure; consider titrating amlodipine to the lowest effective dose or alternative antihypertensive if needed. 
    2. Reduce allopurinol to 100 mg daily (or stop if urate level not target) and arrange urate monitoring. 
    3. Re‑check serum potassium and renal function within 1 week after changes.

    clinician intervention: Consider titrating amlodipine to the lowest effective dose or alternative antihypertensive if needed.

    reasoning: The clinicians intervention is included in the ground truth. It's not called out specifically by it's own number and is included as part of the first intervention. That is acceptable.
    correct: true
    match_id: 1
</example>

<example>
    ground truth interventions 
    1. Discontinue the betamethasone valerate 0.1% cream and continue only the betamethasone 0.1%/fusidic acid 2% cream.
    2. Arrange a follow‑up skin assessment in two weeks to ensure disease control and monitor for any signs of steroid‑induced skin atrophy.

    clinician intervention: Check bloods every 3 months while on methotrexate

    reasoning: The clinician's intervention is not included in the ground truth, so we cannot mark the intervention as correct.
    correct: false
    match_id: null
</example>

<example>
    ground truth interventions: 
    1. Add low‑dose aspirin 75 mg once daily for secondary cardiovascular prevention (unless contraindicated). 
    2. Intensify blood pressure control: either increase enalapril to 10 mg daily and add a thiazide diuretic (e.g., hydrochlorothiazide 12.5 mg once daily) or switch to a combination ACE‑inhibitor/CCB regimen. 
    3. Reduce mirtazapine to 15 mg nightly. Re‑assess blood pressure and fall frequency in 4–6 weeks after changes.

    clinician intervention: Reduce mirtazapine to 15 mg nightly (or consider tapering and switching to a non‑sedating antidepressant) to lower sedation‑related fall risk.

    reasoning: The clinician's intervention goes into more detail about the intervention than the ground truth, however since the only part of the clinician's intervention that's actually the intervention (reduce mirtazapine to 15mg nightly) is included in the ground truth, we can mark the intervention as correct. The rest of the clinician's intervention is not an intervention and just further context.
    correct: true
    match_id: 3
</example>

</examples>

Now please review the following case:

ground truth interventions: 
{ground_truth_interventions}

clinician intervention:
{clinician_intervention}

Please assess whether the intervention is correct and provide your reasoning.

You must respond with valid JSON matching this exact schema:

{{
  "reasoning": "string - detailed explanation with specific evidence",
  "correct": bool,
  "match_id": int | null
}}

Do not include any text outside the JSON object. Do not wrap the JSON in markdown code blocks.
"""
