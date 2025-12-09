FAILURE_CLASSIFICATION_PROMPT = """
You are an expert at assessing the failure modes of a clinician's assessment of a patient's medication profile by comparing it to the ground truth agreed by a panel of experts.

You will be provided with a medication review from a clinician and the ground truth agreed by a panel of experts.

Your task is to understand and document the failure modes, if any, that the clinician's assessment of the patient's medication profile contains.

Here are some rules:
- Only identify failure modes by comparing the clinician's assessment to the ground truth.
- If you believe that there is an additional failure mode but would need to know more about the patient to identify it, then do not include it in the failure modes. This is because we just want to identify failure modes that we can determine by comparing against the ground truth.
- If the clinician's assessment is correct, then there should be no failure modes.
- In your reasoning, include details about the specific failure mode including the full context from the clinician's assessment and the ground truth.
- You should only use your medical knowledge to resolve language differences, rather than anything more specific.

Here are some examples:

<examples>

<example>
    <clinician_review>
    patient review: The patient is an 80‑year‑old female with documented coronary heart disease, hypertension, chronic kidney disease stage 3 (eGFR ~56 mL/min), heart failure, and persistent asthma. At the time of the SMR she is only taking two repeat medications: Luforbec inhaler (2 puffs twice daily) and sublingual glyceryl trinitrate spray for angina. All other long‑term cardiovascular drugs (aspirin, high‑intensity statin, ACE‑inhibitor, beta‑blocker) were stopped and have not been reinstated. Recent blood pressure readings are within target (e.g., 124/68 mmHg) but previous measurements have been higher (up to 147/97 mmHg). Asthma review documented poor adherence, absence of an inhaled corticosteroid, and ongoing symptoms (dry cough, dyspnoea, ACT score 21). The patient is housebound, frail (frailty index 0.33), and has a high mortality risk (69%). Current medication list therefore leaves significant gaps in secondary prevention of CHD and sub‑optimal asthma control, posing substantial risks of cardiovascular events and asthma exacerbations.

    issues that required an intervention:
    - No inhaled corticosteroid for persistent asthma despite ongoing symptoms and documented non‑adherence to inhaled steroids.
    - Absence of antiplatelet therapy for secondary prevention of coronary heart disease.
    - Absence of high‑intensity statin therapy for secondary prevention of coronary heart disease.
    - Absence of ACE‑inhibitor therapy for hypertension, CKD protection and cardiovascular risk reduction.

    intervention: 1. Prescribe an inhaled corticosteroid (e.g., beclometasone 100 µg inhaler, 2 puffs twice daily) and arrange a focused asthma education session to improve adherence.\n2. Restart low‑dose aspirin 75 mg once daily for secondary prevention of CHD, unless a contraindication (e.g., active bleed) is identified.\n3. Restart atorvastatin 40 mg once daily (or 20 mg if tolerance is a concern) for secondary prevention of CHD; monitor liver function and CKD parameters after 4‑6 weeks.\n4. Restart ramipril 2.5 mg once daily, titrating up as tolerated, to control blood pressure, provide renal protection, and reduce cardiovascular risk; re‑check serum creatinine and potassium in 2 weeks.
    </clinician_review>

    <ground_truth>
    issues that required an intervention:
    - No inhaled corticosteroid for persistent asthma despite ongoing symptoms and documented non‑adherence to inhaled steroids.
    - Absence of antiplatelet therapy for secondary prevention of coronary heart disease.

    intervention:
    - No intervention required.

    additional notes:
    - The lack of an inhaled corticosteroid reflects documented non‑adherence; without patient willingness to use inhaled therapy, initiating one is unlikely to be effective.
    - Aspirin was appropriately discontinued because the clinician judged that bleeding risk outweighed benefit in this frail patient.
    </ground_truth>

    <failure_modes>
    - other: This is nuanced because we don't have enough info about the patient preferences and physical robustness to be sure but i suspect this was a reasoned decision based on risk balance. There are no inaccuracies in the information though and the recommendations would be appropriate for someone younger and fitter
</example>

<example>
    <clinician_review>
    patient review: The 87‑year‑old female with atrial fibrillation, rheumatoid arthritis, CKD stage G3a (eGFR 60 mL/min), osteoporosis and diabetes presents for a structured medication review. Current repeat medications include alendronic acid weekly, bisoprolol 2.5 mg at tea‑time and bisoprolol 1.25 mg each morning (total 3.75 mg daily), methotrexate 10 mg weekly, levothyroxine 50 µg each morning, calcium/vitamin‑D supplement, and a short course of lansoprazole. Insulin therapy is ongoing. Recent labs show a markedly elevated gamma‑glutamyl transferase (341 IU/L) and alkaline phosphatase (202 IU/L) with otherwise normal ALT/AST, suggesting cholestatic liver injury. The patient also has a high CRP (91 mg/L) and ESR (55 mm/h) reflecting active inflammation, but no acute infection is documented. The duplicate bisoprolol prescriptions pose a risk of dosing confusion, although the combined dose (3.75 mg) is low. Methotrexate is hepatotoxic and should be reviewed in the context of the abnormal cholestatic enzymes. No anticoagulant is recorded for atrial fibrillation, but the patient is on a palliative care register, so omission may be clinically justified. Overall, two medication‑related safety concerns require immediate action: (1) potential methotrexate‑induced liver injury and (2) duplicate bisoprolol prescriptions.

    issues that required an intervention:
    - Potential methotrexate‑related hepatotoxicity
    - Duplicate bisoprolol prescriptions causing possible dosing error

    intervention: 1. Discontinue methotrexate immediately and arrange repeat liver function testing and hepatology review to assess the cause of the cholestatic picture. 2. Consolidate bisoprolol dosing: replace the two separate scripts (2.5 mg at tea‑time and 1.25 mg each morning) with a single prescription of an appropriate total dose (e.g., 3.75 mg once daily or a standard dose such as 5 mg daily) and cancel the redundant prescription.
    </clinician_review>

    <ground_truth>
    issues that required an intervention:
    - Potential methotrexate‑related hepatotoxicity

    intervention:
    - Review trend in liver function tests and correlate changes with the timeline of methotrexate dosing.
    - Review any previous investigations into cholestatic derangement
    - Repeat liver function tests and review ongoing need for methotrexate

    additional notes:
    - The observed cholestatic LFT pattern (elevated GGT and ALP) is not typical of methotrexate‑induced hepatotoxicity. A more inflammatory picture and a derangement of the ALT would have been expected if this was caused by a drug interaction. Alternative causes should be investigated before attributing it to the drug.
    - The duplicate bisoprolol prescriptions likely reflect an intended total daily dose of 3.75 mg, which cannot be achieved with a single tablet; therefore no dosing error is assumed.
    </ground_truth>

    <failure_modes>
    - knowledge_gap: The observed LFT pattern is not typical of methotrexate-induced hepatotoxicity, which we might have expected the clinician to have known. A more inflammatory picture would have been expected if this was caused by a drug interaction.
</example>

<example>
    <clinician_review>
    patient review: The patient (87F) has CKD stage 3 (eGFR ~54 mL/min/1.73m²) and a recent serum potassium of 6.1 mmol/L indicating hyperkalaemia. She is on candesartan 8 mg twice daily, an ACE‑ARB that can worsen hyperkalaemia in CKD. She also has a history of peptic ulcer disease (duodenal ulcer, ulcer of duodenum) and is currently using topical NSAID (fenbid 10% gel) and a short‑course oral naproxen 250 mg twice daily, both of which increase ulcer and renal risk. Analgesia includes two transdermal opioid patches (Butec 10 µg/h and Butec 5 µg/h) applied concurrently, creating a risk of opioid overdose, especially in a frail, dizzy patient with recent falls. Comprehensive Assessment: Active conditions include atrial fibrillation, hypertension, CKD stage 3, peripheral arterial disease, osteoporotic vertebral collapse, peptic ulcer disease, and recent rectal hemorrhage. Recent labs show hyperkalaemia (K 6.1 mmol/L), elevated creatinine (84 µmol/L), and eGFR 54 mL/min. Medications: Candesartan, Betahistine, Laxido, Butec 10 µg/h patch, Fenbid gel, Paracetamol, Butec 5 µg/h patch (non‑repeat), Anusol HC, Cyclizine, Naproxen.

    issues that required an intervention:
    - Hyperkalaemia (K 6.1 mmol/L) secondary to candesartan in CKD stage 3
    - Concurrent use of two Butec transdermal patches (5 µg/h and 10 µg/h) leading to opioid overdose risk
    - Topical NSAID (fenbid 10% gel) prescribed despite active peptic ulcer disease and CKD
    - Oral naproxen 250 mg BID prescribed in a patient with peptic ulcer disease and CKD
    - Missing gastro‑protective PPI while NSAIDs are being used in a patient with known ulcer disease

    intervention: Immediately discontinue candesartan 8 mg twice daily and arrange repeat renal function and potassium monitoring; cease the 5 µg/h Butec transdermal patch (retain only the 10 µg/h patch) to avoid opioid overdose; stop fenbid 10 % gel and the oral naproxen 250 mg twice daily because of active peptic ulcer disease and CKD; start omeprazole 20 mg once daily for gastro‑protection while any NSAID therapy is required. Review the patient’s analgesic regimen and consider safer alternatives, and reassess the need for anticoagulation in atrial fibrillation after bleeding risk is addressed.
    </clinician_review>

    <ground_truth>
    issues that required an intervention:
    - Hyperkalaemia (K 6.1 mmol/L) secondary to candesartan in CKD stage 3
    - Oral naproxen 250 mg BID prescribed in a patient with peptic ulcer disease and CKD
    - Missing gastro‑protective PPI while NSAIDs are being used in a patient with known ulcer disease

    intervention:
    - Discontinue candesartan 8 mg twice daily and arrange repeat renal function and potassium monitoring within 1–2 weeks.
    - Continue the current Butec transdermal patches for now; arrange a review and discussion with the patient (and palliative‑care team if appropriate) to confirm the analgesic dose is appropriate and consider tapering only if clinically indicated.
    - Stop oral naproxen 250 mg twice daily because of active peptic ulcer disease and CKD.
    - Start omeprazole 20 mg once daily for gastro‑protection while any NSAID therapy is required.
    - Review the overall analgesic regimen (including the fenbid 10 % gel) and consider safer alternatives as needed.
    - Re‑assess the need for anticoagulation in atrial fibrillation after the bleeding risk has been addressed.

    additional notes:
    - The use of two Butec patches (5 µg/h and 10 µg/h) is an intentional dosing strategy, not a duplicate prescription; total dose (15 µg/h) is well below the 40 µg/h maximum.
    - Topical NSAID (fenbid 10 % gel) has minimal systemic absorption and is not considered a safety issue in this patient.
    </ground_truth>

    <failure_modes>
    - reasoning_error: The use of two Butec patches (5 µg/h and 10 µg/h) is an intentional dosing strategy, not a duplicate prescription; total dose (15 µg/h) is well below the 40 µg/h maximum.
</example>

<example>
    <clinician_review>
    patient review: The 76‑year‑old male is on long‑term anticoagulation with warfarin (both 1 mg and 3 mg tablets prescribed) for atrial fibrillation, plus ACE‑inhibitor (perindopril 2 mg), beta‑blocker (bisoprolol 2.5 mg), loop diuretic (furosemide 20 mg), statin (simvastatin 40 mg) and antihistamine (fexofenadine 180 mg). He is being treated for a recent lower‑leg cellulitis (flucloxacillin 500 mg qid started 6 Dec 2024) and a chronic leg ulcer (activa compression stockings, wound care). Recent INR results show therapeutic values but a supratherapeutic INR of 4.1 was recorded, suggesting a period of over‑anticoagulation. Renal function is stable (eGFR ~63 mL/min/1.73 m², potassium 4.9 mmol/L). Blood pressure is well controlled (114/64 mmHg). No contraindications to current antihypertensive regimen are evident. The coexistence of simvastatin with warfarin raises bleed risk but INR is currently within target. Overall the patient is stable but two medication safety concerns are identified: (1) duplicate warfarin tablet strengths creating dosing confusion, and (2) recent INR > 4.0 indicating a need for prompt dose review.

    issues that required an intervention:
    - Duplicate warfarin tablet strengths (1 mg and 3 mg) prescribed simultaneously, creating risk of dosing error
    - Recent supratherapeutic INR of 4.1 indicating over‑anticoagulation

    intervention: 1. Discontinue the 1 mg warfarin tablets and prescribe the required total daily dose using a single tablet strength where possible (e.g., adjust to an appropriate dose of 3 mg tablets or combine 3 mg with 1 mg tablets only after documented calculation). Document the exact total daily warfarin dose in the medication chart to avoid confusion. 2. Review the warfarin dose immediately in response to the INR of 4.1 (17 Jan 2024); hold warfarin for 24‑48 h and re‑check INR in 3‑5 days. If INR returns to therapeutic range, resume warfarin at a reduced dose (e.g., decrease by 10‑20% of the previous total dose) and schedule the next INR check within 7 days. Record the dose adjustment and monitoring plan in the patient’s record.
    </clinician_review>

    <ground_truth>
    issues that required an intervention:
    - Recent supratherapeutic INR of 4.1 indicating over‑anticoagulation

    intervention:
    - Adjust the warfarin prescribing to achieve the required total daily dose using the available UK tablet strengths (0.5 mg, 1 mg, 3 mg, 5 mg) in a clear combination (e.g., 3 mg + 1 mg for a 4 mg total dose)
    - Hold warfarin for 24‑48 hours in response to the INR of 4.1 (17 Jan 2024) and re‑check INR in 3‑5 days.
    - If the repeat INR is within the therapeutic range, resume warfarin at a reduced total daily dose (decrease by 10–20% of the previous dose) and schedule the next INR check within 7 days. Record the dose adjustment and monitoring plan in the patient’s record.

    additional notes:
    - The presence of both 1 mg and 3 mg warfarin tablets is intentional to achieve the required total daily dose; it is not a prescribing error.
    - A single‑tablet regimen is not always feasible because UK warfarin tablets are only available in 0.5, 1, 3 and 5 mg strengths; appropriate combinations should be used.
    - Switching from warfarin to a DOAC may be appropriate for some patients, but contraindications (e.g., recent major bleed, mechanical heart valve) must be evaluated before recommending such a change.
    </ground_truth>

    <failure_modes>
    - knowledge_gap: The clinician was not aware of the limitation caused by the different tablet strengths available in the UK.
    - 
</example>

<example>
    <clinician_review>
    patient review: The 51‑year‑old male has type 2 diabetes (HbA1c 60 mmol/mol), hypertension (recorded BP up to 156/110 mmHg), psoriatic arthritis, a history of peptic ulcer and is a current smoker (1–15 cigarettes/day). Current repeat medications are amlodipine 10 mg daily, metformin 500 mg BID, atorvastatin 20 mg daily, lansoprazole 30 mg daily, sildenafil PRN, methotrexate 10 mg weekly with folic acid 5 mg weekly, and two topical corticosteroids: betamethasone valerate 0.1% cream and a combination betamethasone 0.1%/fusidic acid 2% cream. Liver function tests were last performed in Oct 2019, before methotrexate was restarted in Oct 2020, so no recent monitoring exists. The concurrent use of two potent topical steroids raises the risk of local skin atrophy. Atorvastatin and amlodipine together can increase statin concentrations, potentially heightening myopathy risk, though renal function is normal (eGFR ≈ 90 mL/min/1.73 m²). Blood pressure remains above target despite amlodipine monotherapy. Alcohol intake is moderate, which adds hepatotoxic risk while on methotrexate. Overall, the most urgent safety issue is the duplicate high‑potency topical steroid therapy, which can be resolved immediately; liver function monitoring for methotrexate is required but does not constitute a direct medication change.

    issues that required an intervention:
    - Concurrent use of two high‑potency topical corticosteroids increasing risk of skin atrophy

    issues that did not require an intervention:
    - No recent liver function monitoring for methotrexate therapy
    - Potential statin‑calcium channel blocker interaction (atorvastatin with amlodipine) elevating risk of myopathy

    intervention: Discontinue the betamethasone valerate 0.1% cream and continue only the betamethasone 0.1%/fusidic acid 2% cream; arrange a follow‑up skin assessment in two weeks to ensure disease control and monitor for any signs of steroid‑induced skin atrophy.
    </clinician_review>

    <ground_truth>
    issues that required an intervention:
    - No recent liver function monitoring for methotrexate therapy
    - Concurrent use of two high‑potency topical corticosteroids increasing risk of skin atrophy

    intervention:
    - Discontinue the betamethasone valerate 0.1% cream and continue only the betamethasone 0.1%/fusidic acid 2% cream; arrange a follow‑up skin assessment in two weeks to ensure disease control and monitor for any signs of steroid‑induced skin atrophy.
    - Check bloods every 3 months while on methotrexate (including liver function tests).

    additional notes:
    - Potential statin‑calcium channel blocker interaction (atorvastatin with amlodipine) is low‑dose and not clinically concerning.
    - No recent liver function monitoring for methotrexate therapy was identified as an issue requiring monitoring.
    </ground_truth>

    <failure_modes>
    - safety_critical_omission: It has been 11 months since last bloods, should be 3 months whilst on methotrexate.
</example>

<example>
    <clinician_review>
    patient review: The 67‑year‑old male with severe frailty (CFS 7), advanced dementia, poor mobility, weight loss and residence in a nursing home is currently prescribed a high sedative load: risperidone 1 mg BID, diazepam 5 mg BID, baclofen 10 mg TID and loperamide 2 mg × 2 BID. He also receives omeprazole 20 mg twice daily without a documented gastrointestinal indication. These medication combinations markedly increase the risk of oversedation, respiratory depression and falls, which is especially concerning given his documented mobility problems, severe frailty and dementia. Carbamazepine (Tegretol) is ongoing but electrolytes are currently normal, so no acute issue. The PPI dose is double the usual maintenance dose, adding a potential for bone loss and infection. Overall, the primary safety concerns are the excessive CNS depressant burden and the unnecessarily high dose of omeprazole, both of which warrant prompt deprescribing actions.

    issues that required an intervention:
    - High cumulative CNS depressant load (risperidone, diazepam, baclofen, loperamide) increasing fall and respiratory depression risk
    - Chronic high‑dose omeprazole (40 mg/day) without documented indication, raising risk of fractures, infection and nutrient deficiencies
    - Long‑term benzodiazepine use (diazepam) in a patient with dementia and frailty, increasing cognitive impairment and fall risk

    intervention: 1. Initiate a gradual taper of diazepam (e.g., reduce by 5 mg every 1–2 weeks) aiming for complete cessation within 4–6 weeks. 2. Review the need for baclofen and loperamide; if no current indication for spasticity or diarrhoea, discontinue both. 3. Reduce omeprazole to 20 mg once daily; reassess gastrointestinal symptoms after 4 weeks and consider stopping if none. 4. Arrange a fall‑risk assessment and physiotherapy review following medication changes. 5. Document all changes and communicate with the multidisciplinary team and the patient’s carer.
    </clinician_review>

    <ground_truth>
    issues that required an intervention:
    - High cumulative CNS depressant load (risperidone, diazepam, baclofen, loperamide) increasing fall and respiratory depression risk
    - Chronic high‑dose omeprazole (40 mg/day) without documented indication, raising risk of fractures, infection and nutrient deficiencies
    - Long‑term benzodiazepine use (diazepam) in a patient with dementia and frailty, increasing cognitive impairment and fall risk
    - Statin probably inappropriate in advanced dementia on the palliative care register, would deprescribe

    intervention:
    - Initiate a gradual taper of diazepam (e.g., reduce by 5 mg every 1–2 weeks) aiming for complete cessation within 4–6 weeks.
    - Review the need for baclofen and loperamide; if no current indication for spasticity or diarrhoea, discontinue both.
    - Reduce omeprazole to 20 mg once daily; reassess gastrointestinal symptoms after 4 weeks and consider stopping if none.
    - Discontinue statin therapy as it is likely inappropriate in advanced dementia on the palliative care register.

    additional notes:
    - Diazepam may be required for behaviour management in advanced dementia, but a taper is still recommended as per clinician.
    - Statin deprescribing is intended to avoid unnecessary medication burden in a patient on a palliative care pathway.
    </ground_truth>

    <failure_modes>
    - non_critical_omission: The clinician missed the opportunity to deprescribe the statin here.
</example>

<example>
    <clinician_review>
    patient review: The patient is a 67‑year‑old man with a long history of ophthalmology follow‑up, pre‑diabetes (non‑diabetic hyperglycemia with HbA1c 39‑42 mmol/mol), hypertension (recorded in the hypertension register) and a past peptic ulcer. The only repeat medication currently prescribed is latanoprost eye drops. Recent labs show stable renal function (eGFR 70‑85 mL/min/1.73 m²) and normal electrolytes. Blood pressure recordings show good home values (124/76 mmHg) but an elevated clinic reading of 140/90 mmHg, and there is no antihypertensive drug on the medication list. No drug‑drug interactions, dosing errors, or missing protective agents are identified. The main actionable issue is untreated hypertension, which carries a substantial cardiovascular risk in this age group and with his pre‑diabetic status.

    issues that required an intervention:
    - Uncontrolled hypertension with no antihypertensive therapy

    intervention: Start a low‑dose ACE inhibitor, e.g., prescribe ramipril 2.5 mg orally once daily, and arrange repeat blood pressure measurement in 2 weeks to assess response. Provide lifestyle advice (salt restriction, regular exercise) and schedule a follow‑up review of BP and renal function after 4 weeks.
    </clinician_review>

    <ground_truth>
    no issues required an intervention

    no intervention was required

    additional notes:
    - Uncontrolled hypertension was not confirmed; home blood pressure readings are considered more accurate and are within normal range.
    - No antihypertensive therapy is required at this time; continue routine monitoring.
    </ground_truth>

    <failure_modes>
    - input_processing_error: UK guidelines would say home readings more accurate than in clinic so NICE says only treat if home readings >135/85 (he is below treatment threshold)
</example>

</examples>

Now please review the following case:

<clinician_review>
{clinician_review}
</clinician_review>

<ground_truth>
{ground_truth}
</ground_truth>

Please assess whether the ground truth is correct and provide your reasoning.

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
"""
