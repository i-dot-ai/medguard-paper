INTERVENTION_SPLITTING_PROMPT = """
You are an expert at identifying the distinct interventions present in a paragraph of text written by a clinician.

You will be provided with an intervention proposed by a clinician.

Your task is to identify and list the distinct interventions within the paragraph of text written by the clinician.

Where the original paragraph contains numbers, you should respect this numbering.

Where the original paragraph does not contain numbers, you should use your judgement to record the distinct clinical interventions.

Here are some examples:

<examples>

<example>
    intervention: Prescribe an inhaled corticosteroid (e.g., beclometasone 100 µg inhaler, 2 puffs twice daily) and arrange a focused asthma education session to improve adherence. Restart atorvastatin 40 mg once daily (or 20 mg if tolerance is a concern) for secondary prevention of CHD; monitor liver function and CKD parameters after 4‑6 weeks. Restart ramipril 2.5 mg once daily, titrating up as tolerated, to control blood pressure, provide renal protection, and reduce cardiovascular risk; re‑check serum creatinine and potassium in 2 weeks.

    intervention list: 
    - Prescribe an inhaled corticosteroid (e.g., beclometasone 100 µg inhaler, 2 puffs twice daily) and arrange a focused asthma education session to improve adherence.
    - Restart atorvastatin 40 mg once daily (or 20 mg if tolerance is a concern) for secondary prevention of CHD; monitor liver function and CKD parameters after 4‑6 weeks.
    - Restart ramipril 2.5 mg once daily, titrating up as tolerated, to control blood pressure, provide renal protection, and reduce cardiovascular risk
    - Re‑check serum creatinine and potassium in 2 weeks.

</example>

<example>
    intervention: Order serum creatinine, urea and calculate eGFR/CrCl. If eGFR falls <30 mL/min/1.73 m² (or CrCl <30 mL/min), reduce apixaban to 2.5 mg twice daily per dose‑adjustment guidelines; otherwise continue current dose and repeat renal monitoring annually.

    intervention list: 
    - Order serum creatinine, urea and calculate eGFR/CrCl. If eGFR falls <30 mL/min/1.73 m² (or CrCl <30 mL/min), reduce apixaban to 2.5 mg twice daily per dose‑adjustment guidelines; otherwise continue current dose and repeat renal monitoring annually.
</example>


<example>
    intervention: 1. Discontinue the duplicate furosemide prescription and reduce the total daily dose to 80 mg (e.g., 40 mg twice daily) to avoid over‑diuresis. 2. Initiate an ACE inhibitor such as ramipril 2.5 mg once daily (titrating to target) to achieve blood pressure control and provide renal protection. 3. Reduce the dose of gabapentin to 300 mg three times daily.
    
    intervention list: 
    - Discontinue the duplicate furosemide prescription and reduce the total daily dose to 80 mg (e.g., 40 mg twice daily) to avoid over‑diuresis. 
    - Initiate an ACE inhibitor such as ramipril 2.5 mg once daily (titrating to target) to achieve blood pressure control and provide renal protection. 
    - Reduce the dose of gabapentin to 300 mg three times daily.
</example>


<example>
    intervention: Stop atenolol 100 mg and reassess blood pressure; consider titrating amlodipine to the lowest effective dose or alternative antihypertensive if needed. Reduce allopurinol to 100 mg daily (or stop if urate level not target) and arrange urate monitoring. Re‑check serum potassium and renal function within 1 week after changes.

    intervention list: 
    - Stop atenolol 100 mg and reassess blood pressure; consider titrating amlodipine to the lowest effective dose or alternative antihypertensive if needed. 
    - Reduce allopurinol to 100 mg daily (or stop if urate level not target) and arrange urate monitoring. 
    - Re‑check serum potassium and renal function within 1 week after changes.
</example>


<example>
    intervention: Discontinue the betamethasone valerate 0.1% cream and continue only the betamethasone 0.1%/fusidic acid 2% cream; arrange a follow‑up skin assessment in two weeks to ensure disease control and monitor for any signs of steroid‑induced skin atrophy.

    intervention list: 
    - Discontinue the betamethasone valerate 0.1% cream and continue only the betamethasone 0.1%/fusidic acid 2% cream.
    - arrange a follow‑up skin assessment in two weeks to ensure disease control and monitor for any signs of steroid‑induced skin atrophy.
</example>


<example>
    intervention: 1. Add low‑dose aspirin 75 mg once daily for secondary cardiovascular prevention (unless contraindicated). 2. Intensify blood pressure control: either increase enalapril to 10 mg daily and add a thiazide diuretic (e.g., hydrochlorothiazide 12.5 mg once daily) or switch to a combination ACE‑inhibitor/CCB regimen. 3. Reduce mirtazapine to 15 mg nightly. Re‑assess blood pressure and fall frequency in 4–6 weeks after changes.

    intervention list: 
    - Add low‑dose aspirin 75 mg once daily for secondary cardiovascular prevention (unless contraindicated). 
    - Intensify blood pressure control: either increase enalapril to 10 mg daily and add a thiazide diuretic (e.g., hydrochlorothiazide 12.5 mg once daily) or switch to a combination ACE‑inhibitor/CCB regimen. 
    - Reduce mirtazapine to 15 mg nightly. Re‑assess blood pressure and fall frequency in 4–6 weeks after changes.
</example>

<example>
    intervention: 

    intervention list:

    [if the intervention is blank, just return an empty list]
</example>
</examples>

Please record the distinct interventions in this paragraph provided by a clinician:
{clinician_intervention}


You must respond with valid JSON matching this exact schema:

{{
  "interventions": ["string", "string", ...]
}}

Do not include any text outside the JSON object. Do not wrap the JSON in markdown code blocks.


"""
