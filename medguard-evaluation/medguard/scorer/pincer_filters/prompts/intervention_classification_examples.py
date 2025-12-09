INTERVENTION_CLASSIFICATION_EXAMPLES = """
<example>
    Flagged Clinical Issue: Methotrexate prescribed without folic acid

    MedGuard Patient Summary: The patient is a 60‑year‑old female with atrial fibrillation, heart failure, chronic kidney disease (eGFR 59 mL/min/1.73m²), rheumatoid arthritis and multiple frailty deficits (dizziness, falls risk, anaemia). Currently active medications are Co‑codamol 15 mg/500 mg tablets (PRN up to 8 tablets/day), Estriol vaginal cream and Methotrexate 20 mg weekly (8×2.5 mg tablets). Recent labs show an acute kidney injury warning stage, normal liver function but borderline renal function. Methotrexate is being given at a full weekly dose despite eGFR <60 mL/min/1.73m² and without concomitant folic acid, raising risk of toxicity. The high‑dose opioid‑paracetamol preparation adds sedative load in a frail patient with dizziness and a history of irregular pulse, increasing fall risk. No protective co‑prescriptions (e.g., folic acid) or recent renal monitoring specific to methotrexate are documented.

    MedGuard Identified the following issues, all of which were then reviewed by a clinician to assess their correctness:

    Issue 1:
    Issue Identified by MedGuard: Methotrexate dose unsafe for current renal function (eGFR 59) with acute kidney injury warning
    Evidence provided by MedGuard: eGFR 59 mL/min/1.73m² and AKI warning stage; Methotrexate 20 mg weekly currently being taken
    Clinician reasoning: Although, max dose is 25mg and eGFR 45-59 i'd consider 25% dose reduction so she's still in range. As a general rule, eGFR>60 would be full dose so she's only just under that threshold, i wouldn't be too concerned. 
    The clinician agreed with MedGuard's assessment of this issue

    Issue 2:
    Issue Identified by MedGuard: High‑dose codeine‑paracetamol (Co‑codamol) in frail patient with dizziness and fall risk
    Evidence provided by MedGuard: Co‑codamol prescribed PRN up to 8 tablets/day; frailty deficits include dizziness, falls, and recent low blood pressure readings; no recent review limiting opioid use
    Clinician reasoning: She is only 60 and has rheumatoid arthritis so will experience pain, i think this is probably being overly cautious, i would not describe her as frail per se
    The clinician disagreed with MedGuard's assessment of this issue

    The clinician then assessed whether MedGuard correctly identified the flagged clinical issue or not:

    reasoning: Although MedGuard mentioned that there were no protective co-prescriptions to methotrexate in their patient summary, because MedGuard did not pull this out as a specific issue the clinician concluded that MedGuard did not correctly identify the flagged issue
    correct: false

    The clinician then assessed whether MedGuard's intervention would be appropriate for the patient:

    MedGuard did not believe an intervention was required

    reasoning: MedGuard did not propose an intervention for this patient, believing that the patient did not need one. This is a critical issue as it means that MedGuard has missed a key safety concern.
    correct: false

    Failure mode:
    - safety_critical_omission: MedGuard did not identify a safety-critical issue that required an intervention.
</example>

<example>
    MedGuard Patient Summary: The 79‑year‑old woman has active hypertension, type 2 diabetes and recent pelvic surgery - recent vaginal hysterectomy. She is currently prescribed omeprazole, rosuvastatin, lisinopril, metformin, intravaginal estrogen, and two overlapping prednisolone regimens (4 mg daily from 1 mg tablets plus 5 mg daily from a separate 5 mg tablet, total 9 mg/day). She also has a repeat prescription for co‑codamol 15 mg/500 mg with instructions "One or Two to be taken four times a day when required". Recent labs show eGFR 72 mL/min/1.73 m², HbA1c 55 mmol/mol and normal liver function. The main safety concerns are the potentially excessive co‑codamol dose for an elderly postoperative patient and the concurrent prednisolone courses, which increase risk of hyperglycaemia, infection and impaired wound healing. Both issues require prompt medication adjustment.

    Flagged Clinical Issue: 17 - Oral prednisolone prescribed at a dose ≥7.5mg daily for more than 3 months to the over 65s without co-prescription of osteoporosis-preventing treatments

    MedGuard Identified the following issues, all of which were then reviewed by a clinician to assess their correctness:

    Issue 1:
    Issue Identified by MedGuard: Potential overdose and unsafe dosing of co‑codamol in an elderly post‑operative patient
    Evidence provided by MedGuard: Co‑codamol 15 mg/500 mg tablets prescribed as repeat medication with dosage "One or Two to be taken four times a day when required"; this could allow up to 8 tablets/day (4 g paracetamol, 120 mg codeine), exceeding recommended limits for patients >65 years
    Clinician reasoning: agree dose is high but she has just undergone major abdominal surgery so provided this is monitored and gradually weaned, this might be a legitimate analgesic strategy
    The clinician agreed with MedGuard's assessment of this issue

    Issue 2:
    Issue Identified by MedGuard: Concurrent prednisolone regimens resulting in total 9 mg/day in a diabetic hypertensive elder post‑surgery
    Evidence provided by MedGuard: Prednisolone 1 mg tablets, four tablets daily and Prednisolone 5 mg tablet, one daily are both active; total glucocorticoid dose 9 mg/day
    Clinician reasoning: total daily dose intended to be 9mg, probably will be gradually weaned over time, steroids are necessary treatment for PMR so although they come with risks, the benefit outweighs the risk
    The clinician disagreed with MedGuard's assessment of this issue

    The clinician then assessed whether MedGuard correctly identified the flagged clinical issue or not:

    reasoning: While MedGuard didn't mention all aspects of the flagged issue: namely the specific dose, the duration of three months, or explicitly call out the age of the patient. Indeed, the clinician further disagreed with MedGuard on that specific issue. Nevertheless, the clinician concluded that MedGuard did correctly identify the flagged issue. Because this stage is assessment of whether MedGuard can identify the flagged issue, they concluded MedGuard had done this correctly.
    correct: true

    The clinician then considered whether MedGuard's intervention would be appropriate for the patient:

    MedGuard believed an intervention was required

    MedGuard's intervention: Reduce co‑codamol to a maximum of 2 tablets per dose and no more than 4 tablets per day (≤2 g paracetamol/≤60 mg codeine) and discuss alternative analgesia; arrange a prednisolone taper plan to consolidate the two courses into a single, lower‑dose regimen with a clear wean schedule and ensure close blood‑glucose monitoring post‑operatively.

    reasoning: Medguard flagged prednisolone but did not mention need for bone protection in its reasoning so hasn't concurred with the clinical error rules exactly. weaning is only possible gradually and according to treatment response, they may be required long-term. It's not possible to mandate a weaning course without monitoring response. Instead the intervention should follow the NICE guidelines and suggest treatment may be required for 1-2 years and tapering is done very slowly and only when symptoms resolved, she is only 3m into treatment. The tapering advice given is too enthusiastic.
    correct: false

    Failure mode:
    - knowledge_gap
</example>

<example>
    MedGuard Patient Summary: The patient is a 70‑year‑old female with atrial fibrillation, COPD, and recent lower respiratory tract infection. At the SMR she is actively prescribed bempedoic acid, verapamil MR, ikervis eye drops, bisoprolol 2.5 mg, glyceryl trinitrate spray, and a short course of amoxicillin. Recent labs show stable renal function (eGFR 79 mL/min/1.73 m²) and normal liver enzymes. The most pressing safety concern is the concurrent use of two rate‑controlling agents—verapamil and bisoprolol—without recent ECG monitoring, which raises the risk of excessive bradycardia or AV block, especially given the patient’s atrial fibrillation and recent addition of bisoprolol. No other acute safety‑critical issues were identified.

    Flagged Clinical Issue: 38 - Prescription of verapamil to a patient who is also receiving a beta-blocker

    MedGuard Identified the following issues, all of which were then reviewed by a clinician to assess their correctness:

    Issue 1:
    Issue Identified by MedGuard: Concurrent verapamil and bisoprolol therapy risking bradycardia/AV block
    Evidence provided by MedGuard: Verapamil 240 mg MR repeat prescription (still active); Bisoprolol 2.5 mg repeat prescription active; recent vitals show HR 76 bpm, BP 130/80 mmHg; atrial fibrillation documented in QOF register and recent ECG not recorded.
    The clinician agreed with MedGuard's assessment of this issue

    The clinician then assessed whether MedGuard correctly identified the flagged clinical issue or not:

    reasoning: This case was clear-cut; MedGuard identified a single issue which was the flagged issue and was correct in doing so.
    correct: true

    The clinician then assessed whether MedGuard's intervention would be appropriate for the patient:

    MedGuard believed an intervention was required.

    MedGuard's intervention: Discontinue verapamil 240 mg MR immediately and continue bisoprolol 2.5 mg for rate control; arrange a baseline ECG within 7 days and review heart rate and blood pressure after the change to ensure adequate rate control and absence of bradycardia.

    reasoning: The intervention directly addresses the flagged issue and is a correct intervention.
    correct: true
</example>

<example>
    MedGuard Patient Summary: The patient is an 81‑year‑old female with atrial fibrillation on warfarin, chronic kidney disease (eGFR ~36 mL/min/1.73m2), hypertension treated with telmisartan, bisoprolol and doxazosin, and depression treated with low‑dose citalopram. Recent data show a low blood pressure reading (105/60 mmHg) together with recorded dizziness, and frailty deficits including hypotension/syncope and fragility fracture. A course of doxycycline was started on for a productive cough. The most urgent safety problem is the lack of recent INR monitoring for warfarin, especially important now that doxycycline (which can raise INR) has been added. There is also a known interaction between warfarin and citalopram that raises bleeding risk, and the combined antihypertensive regimen may be causing symptomatic hypotension.

    Flagged Clinical Issue: 33 - Concurrent use of warfarin and any antibiotic without monitoring the INR within 5 days

    MedGuard Identified the following issues, all of which were then reviewed by a clinician to assess their correctness:

    Issue 1:
    Issue Identified by MedGuard: Warfarin therapy with no recent INR monitoring and recent initiation of doxycycline (potential INR elevation)
    Evidence provided by MedGuard: Warfarin active; last INR recorded (2.5); doxycycline started; no INR values after 2018.
    Clinician reasoning: as above, needs INR
    The clinician agreed with MedGuard's assessment of this issue

    Issue 2:
    Issue Identified by MedGuard: Increased bleeding risk from concurrent warfarin and citalopram
    Evidence provided by MedGuard: Warfarin active; citalopram 10 mg daily active; known pharmacodynamic interaction increasing bleed risk.
    Clinician reasoning: 
    The clinician agreed with MedGuard's assessment of this issue

    Issue 3:
    Issue Identified by MedGuard: Possible antihypertensive‑induced hypotension causing dizziness
    Evidence provided by MedGuard: Active antihypertensives: telmisartan 40 mg daily, bisoprolol 2.5 mg BID, doxazosin 1 mg daily; BP 105/60 mmHg; dizziness recorded; frailty deficits include hypotension/syncope.
    Clinician reasoning: blood pressure targett should be relaxed to reduce falls risk
    The clinician agreed with MedGuard's assessment of this issue

    The clinician then assessed whether MedGuard correctly identified the flagged clinical issue or not:

    reasoning: Although MedGuard did not call out the specific conditions in the flagged issue, in particular the need for an INR monitoring within 5 days, they concluded that MedGuard had nevertheless clearly identified the issue at hand.
    correct: true

    The clinician then considered whether MedGuard's intervention would be appropriate for the patient:

    MedGuard believed an intervention was required: True

    MedGuard's intervention: Arrange an urgent INR test (preferably today) and review warfarin dose in view of the new doxycycline course; if INR is elevated, withhold or reduce warfarin and re‑check. Simultaneously, reassess the need for citalopram – consider dose reduction or temporary discontinuation to lower bleed risk, and increase INR monitoring frequency. Perform orthostatic blood pressure measurement and consider deprescribing one antihypertensive (e.g., stop doxazosin) to alleviate hypotension, with repeat BP check in 1 week.

    reasoning: The intervention is specific and actionable, it addresses the flagged clinical issue and overall remains a correct intervention.
    correct: true
</example>

<example>
    MedGuard Patient Summary: The 86‑year‑old female is currently prescribed repeat medications of lansoprazole 15 mg ODT daily, amlodipine 5 mg daily, aspirin 300 mg daily, and atorvastatin 20 mg chewable tablets taken twice daily (total 40 mg). Recent labs (Nov 2020) show preserved renal function (eGFR ~83 mL/min) and mild hyponatraemia (131 mmol/L) but a persistent moderate anaemia (Hb ~95‑99 g/L). No acute events such as bleeding, falls, or renal deterioration are documented. The following medication safety concern is evident: concomitant amlodipine 5 mg with a high‑dose atorvastatin 40 mg increases statin exposure and risk of myopathy.

    Flagged Clinical Issue: 2 - Prescription of aspirin at a dose >75mg daily for ≥1 month in a patient aged >65 years

    MedGuard Identified the following issue, which was then reviewed by a clinician to assess their correctness:

    Issue 1:
    Issue Identified by MedGuard: Atorvastatin 40 mg daily combined with amlodipine 5 mg raises atorvastatin plasma levels, increasing risk of myopathy
    Evidence provided by MedGuard: Active repeat prescriptions: Atorvastatin 20 mg tablets twice daily (total 40 mg) and Amlodipine 5 mg daily; known pharmacokinetic interaction between amlodipine and higher‑dose atorvastatin
    Clinician reasoning: the interaction is less for atorva than for simva. BNF does not suggest switch is needed. 40mg is acceptable dose, i'd only consider a switch at high dose /eg 80mg)
    The clinician disagreed with MedGuard's assessment of this issue

    The clinician then assessed whether MedGuard correctly identified the flagged clinical issue or not:

    reasoning: Although MedGuard mentions the high aspirin prescription dosage in their patient summary, MedGuard made no reference to the flagged issue.
    correct: false

    The clinician then assessed whether MedGuard's intervention would be appropriate for the patient:

    MedGuard did believe an intervention was required.

    MedGuard's intervention: Reduce atorvastatin total daily dose from 40 mg to 20 mg (take one 20 mg chewable tablet daily) or switch to a statin with less interaction (e.g., pravastatin 40 mg daily).

    reasoning: The key patient concern here is the prescription of aspirin at a dose >75mg daily for ≥1 month in a patient aged >65 years. MedGuard's intervention does not address this issue at all and instead focuses on an issue that isn't itself necessary.
    correct: false

    Failure mode:
    - safety_critical_omission: MedGuard did not identify a safety-critical issue that required an intervention. Here this took the form of not identifying the flagged issue.
    - knowledge_gap: MedGuard suggested reducing the atorvastatin dose, but the BNF suggests that a switch is not necessary in this case and the current dose is acceptable.
</example>

<example>
    MedGuard Patient Summary: The 65‑year‑old male has active coronary artery disease, heart failure, hypertension, type 2 diabetes, asthma and a history of peptic ulcer. He is currently on several repeat prescriptions: ramipril, omeprazole, co‑amilofruse (replaced by separate furosemide 40 mg and amiloride 5 mg), aspirin, amlodipine 10 mg, atorvastatin 80 mg, gliclazide 80 mg and a second gliclazide 40 mg tablet, cetirizine, terbutaline inhaler, Sirdupla inhaler and topical steroids. Recent labs show eGFR 81 mL/min, potassium 4.3 mmol/L and HbA1c 70 mmol/mol, indicating poor glycaemic control but stable renal function. Two safety‑significant issues are identified: (1) duplicate gliclazide prescriptions causing a risk of hypoglycaemia, and (2) a known pharmacokinetic interaction between high‑dose atorvastatin 80 mg and amlodipine 10 mg increasing the risk of statin‑related myopathy.

    Flagged Clinical Issue: 37 - Prescription of a potassium salt or potassium-sparing diuretic (excluding aldosterone antagonists) to a patient who is also receiving an ACE inhibitor or angiotensin II receptor antagonist

    MedGuard Identified the following issues, all of which were then reviewed by a clinician to assess their correctness:

    Issue 1:
    Issue Identified by MedGuard: Duplicate gliclazide prescriptions (80 mg + 40 mg daily) risk of hypoglycaemia
    Evidence provided by MedGuard: Active repeat prescriptions: Gliclazide 80 mg tablets and Gliclazide 40 mg tablets both marked as repeat and being taken at SMR date; HbA1c 70 mmol/mol shows poor control
    Clinician reasoning: max dose of standard release is 160mg so the total daily dose is below that which is acceptable. 
    The clinician disagreed with MedGuard's assessment of this issue

    Issue 2:
    Issue Identified by MedGuard: Statin‑amlodipine interaction increasing risk of myopathy
    Evidence provided by MedGuard: Atorvastatin 80 mg nightly, together with Amlodipine 10 mg daily; known interaction raises atorvastatin levels; liver function normal (ALT 25 IU/L, ALP 146 IU/L in 2020) but no CK monitoring reported
    Clinician reasoning: The risk of stain amlodipine interaction is highest for simvastatin. The risk of interaction with high dose atorvastatin (as in this case) is present, but lower than with simvastatin. It is possible to change to prav, fluva or rosuv as an alternative statin but i don't consider this an essential switch in the context of normal LFTs and provided the patient has no complaints of muscle pain
    The clinician disagreed with MedGuard's assessment of this issue

    Issue 3:
    Issue Identified by MedGuard: Potential hyperkalaemia risk from ACE inhibitor + loop diuretic + amiloride combination
    Evidence provided by MedGuard: Ramipril 5 mg daily (repeat), Furosemide 40 mg daily and Amiloride 5 mg daily active as of 2020; potassium 4.3 mmol/L within normal range but requires ongoing monitoring
    Clinician reasoning: correctly indicating it needs monitoring but is not an absolute contraindication
    The clinician agreed with MedGuard's assessment of this issue

    The clinician then assessed whether MedGuard correctly identified the flagged clinical issue or not:

    reasoning: MedGuard identified in Issue 3 the presence of amiloride (a potassium-sparing diuretic) alongside ramipril (an ACE inhibitor). This matches the flagged issue. Although MedGuard further mentions the presence of a loop diuretic, this doesn't distract from the fact that MedGuard has correctly identified the issue at hand.
    correct: true

    The clinician then assessed whether MedGuard's intervention would be appropriate for the patient:

    MedGuard believed an intervention was required

    MedGuard's intervention: 1) Discontinue the Gliclazide 40 mg tablets to eliminate duplicate sulfonylurea dosing; titrate the remaining Gliclazide 80 mg as needed under review. 2) Reduce atorvastatin dose from 80 mg to 40 mg nightly (or switch to a statin with lower interaction risk) to mitigate the amlodipine‑statin interaction. 3) Arrange repeat serum potassium and renal function tests in 2 weeks to monitor for hyperkalaemia with the ACE‑inhibitor/diuretic/amiloride regimen.

    reasoning: The gliclazide total daily dose is intentional not duplicate, it is necessary to combine two lower dose tablets sometimes. It is below the max dose and there is no evidence of recurrent hypoglycaemia. I don't think atorvastatin dose reduction is necessary and the patient needs the lipid management for long term risk reduction. Agree re monitoring renal function but probably not as urgently required as suggested here. Instead, the intervention should suggest biannual monitoring of LFTs and renal function
    correct: true

    failure_mode:
    - reasoning_error: MedGuard misidentified both the duplicate gliclazide prescription (it was an intentional and appropriate dosing—two tablet strengths adding to a below-max total) and the necessity to reduce/statin switch for atorvastatin (not essential in this setting, per BNF and clinician judgement); did not give the correct priority to the flagged issue. Correct intervention would focus on periodic monitoring, not medication discontinuation/dose reduction.

    [n.b. note how the intervention is marked as correct, because it addresses the flagged issue, even if the reasoning has identified issues with some other parts of the intervention]
</example>

<example>
    MedGuard Patient Summary: The patient is a 68‑year‑old female with atrial fibrillation, coronary heart disease, heart failure, hypertension, diabetes, peptic ulcer disease and a history of falls. On the day of the structured patient review she had a blood pressure of 176/93 mmHg, indicating uncontrolled hypertension, and a BMI of 36 kg/m2. She is actively taking amlodipine 5 mg once daily and ibuprofen 400 mg three times daily. The ibuprofen use is contraindicated given her documented peptic ulcer disease, posing a significant risk of gastrointestinal bleeding. Both the high BP and the NSAID prescription represent current safety concerns that need immediate remediation.

    Flagged Clinical Issue: 28 - Prescription of an NSAID, without co-prescription of an ulcer-healing drug, to a patient with a history of peptic ulceration

    MedGuard Identified the following issues, all of which were then reviewed by a clinician to assess their correctness:

    Issue 1:
    Issue Identified by MedGuard: Uncontrolled hypertension (BP 176/93 mmHg)
    Evidence provided by MedGuard: GP blood pressure measurement recorded systolic 176 mmHg and diastolic 93 mmHg.
    Clinician reasoning: agree needs optimization of BP treatment
    The clinician agreed with MedGuard's assessment of this issue

    Issue 2:
    Issue Identified by MedGuard: Ibuprofen prescribed despite peptic ulcer disease
    Evidence provided by MedGuard: Active ibuprofen 400 mg TID while peptic ulcer is listed among frailty deficits.
    Clinician reasoning: regular NSAID without gastroprotection is a risk, particularly given previous ulcer. It will also contribute to high blood pressure. 
    The clinician agreed with MedGuard's assessment of this issue

    The clinician then assessed whether MedGuard correctly identified the flagged clinical issue or not:

    reasoning: Given the evidence raised by MedGuard in issue 2 it's clear that MedGuard has identified the un-mitigated prescription of an NSAID to a patient with peptic ulcer disease. They judged that, despite not calling out the lack of co-prescription, it was evident from MedGuard's identification of this issue that they would have also recommended that.
    correct: true

    The clinician then assessed whether MedGuard's intervention would be appropriate for the patient:

    MedGuard did believe an intervention was required.

    MedGuard's intervention: Stop ibuprofen immediately and prescribe omeprazole 20 mg once daily for gastro‑protection; offer paracetamol as alternative analgesic. Review antihypertensive regimen and add an ACE‑inhibitor (e.g., ramipril 2.5 mg daily) or another agent to achieve target BP, with repeat BP check in 1‑2 weeks.

    reasoning: Although the clinician agreed with MedGuard's intervention, they did note that it's easier said than done to de-escalate someone's analgesia, particularly if they have ongoing pain from osteoarthritis. It may be that an intra-articular steroid injection might be a better alternative. 
    correct: true

    failure_mode:
    - non_critical_omission: difficulty in clinical practice of de-escalating a treatment for pain, limited alternative options, accessing joint injection service not easy due to healthcare constraints

    [n.b. note how the intervention is marked as correct, because it addresses the flagged issue, even if the reasoning has identified issues with some other parts of the intervention]
</example>

<example>
    MedGuard Patient Summary: The 76‑year‑old female has several active medications that raise safety concerns. Most urgent is the high dose amitriptyline (100 mg nightly) prescribed despite documented ischaemic heart disease and a history of hypertension, which places her at risk of cardiac arrhythmia and anticholinergic side effects. A second significant issue is duplicate therapy with sulfasalazine: both Sulfasalazine 500 mg three times daily and Salazopyrin EN‑Tabs 500 mg three times daily are active, effectively doubling the sulfasalazine exposure and increasing risk of bone‑marrow suppression and hepatotoxicity. Additional concerns include the weekly azithromycin course combined with amitriptyline (both QT‑prolonging agents) and regular morphine use in a frail patient with mobility problems, heightening fall and respiratory depression risk. Renal function is currently adequate (eGFR 82 mL/min/1.73 m²), and electrolytes are stable, but continued monitoring is required for the loop diuretic and ACE‑like therapy. Overall, the medication regimen requires prompt optimisation to mitigate cardiac, hematologic and fall risks.

    Flagged Clinical Issue: 43 - Patients aged >75 years on loop diuretics who have not had a U+E in the previous 15 months

    MedGuard Identified the following issues, all of which were then reviewed by a clinician to assess their correctness:

    Issue 1:
    Issue Identified by MedGuard: High-dose amitriptyline (100 mg nightly) in a patient with ischaemic heart disease
    Evidence provided by MedGuard: Amitriptyline 50 mg tablets, two taken at night – active; documented ischaemic heart disease among frailty deficits; recent ECG not provided; dose exceeds typical geriatric maximum of 75 mg
    Clinician reasoning: i'd say 50mg-max 75mg in older people with heart disease
    The clinician agreed with MedGuard's assessment of this issue

    Issue 2:
    Issue Identified by MedGuard: Duplicate sulfasalazine therapy (Sulfasalazine and Salazopyrin EN‑Tabs)
    Evidence provided by MedGuard: Sulfasalazine 500 mg three times daily and Salazopyrin EN‑Tabs 500 mg three times daily both active; same active ingredient leading to double dosing
    The clinician agreed with MedGuard's assessment of this issue

    Issue 3:
    Issue Identified by MedGuard: Concurrent QT‑prolonging drugs (amitriptyline + azithromycin weekly)
    Evidence provided by MedGuard: Amitriptyline 100 mg nightly and Azithromycin 250 mg three times a week both active; both known to prolong QT interval; patient has cardiac disease
    Clinician reasoning: although not an absolute contraindication, just needs monitoring. It's an added reason to want to reduce and discontinue the amitriptyline
    The clinician agreed with MedGuard's assessment of this issue

    Issue 4:
    Issue Identified by MedGuard: Regular morphine use in frail patient with mobility problems
    Evidence provided by MedGuard: Morphine sulfate oral solution 5 ml every 4–6 h PRN, max 30 ml/day – active; frailty deficits include mobility and transfer problems; risk of sedation, falls, respiratory depression
    Clinician reasoning: But challenging for someone with significant pain in absence of alternatives
    The clinician agreed with MedGuard's assessment of this issue

    The clinician then assessed whether MedGuard correctly identified the flagged clinical issue or not:

    reasoning: Despite identification of several issues, all of which the clinician agreed with MedGuard on, MedGuard nevertheless did not identify the flagged issue in this patient.
    correct: false

    The clinician then assessed whether MedGuard's intervention would be appropriate for the patient:

    MedGuard believed an intervention was required.

    MedGuard's intervention: 1. Discontinue Salazopyrin EN‑Tabs immediately and continue only Sulfasalazine 500 mg three times daily (or vice‑versa) to avoid duplicate sulfasalazine exposure. 2. Reduce amitriptyline to 25 mg nightly (or stop if not essential) and arrange a baseline ECG to assess QT interval before any further use. 3. Review the need for weekly azithromycin; if continued, ensure ECG monitoring and consider alternative antibiotic prophylaxis. 4. Re‑evaluate morphine dosing given frailty; consider reducing dose or switching to a safer analgesic, and implement regular falls risk assessment and respiratory monitoring.

    reasoning: The clinician mostly agreed with MedGuard's intervention, but noted that they needed an up to date ECG and renal function to make a complete assessment.
    correct: true

    failure_mode:
    - non_critical_omission: MedGuard didn't note the need for an up to date ECG and renal function to make a complete assessment.
</example>

</example>
    Flagged Clinical Issue: Prescription of a long-acting beta-2 agonist inhaler to a patient with asthma who is not also prescribed an inhaled corticosteroid

    MedGuard Patient Summary: The patient is a 65-year-old male with asthma, peptic ulcer history and recent prescriptions for salmeterol, allopurinol, simvastatin, salbutamol, montelukast and lansoprazole. The most urgent safety issue is salmeterol (a long‑acting beta‑agonist) being prescribed without any inhaled corticosteroid, which is contraindicated and risks severe asthma exacerbations. Additionally, both allopurinol and simvastatin lack recent renal and liver function monitoring respectively; the latest eGFR and LFTs are from January 2023, over two years old, making dose assessment uncertain. No other acute events or critical drug‑drug interactions are evident.

    MedGuard Identified the following issues, all of which were then reviewed by a clinician to assess their correctness:

    Issue 1:
    Issue Identified by MedGuard: LABA (salmeterol) prescribed without concomitant inhaled corticosteroid
    Evidence provided by MedGuard: Active Salmeterol 25 µg inhaler prescribed from 30‑Dec‑2024 (Event 1). No active inhaled steroid; fluticasone stopped 13‑Oct‑2024 and marked not taken (Event 7).
    Clinician reasoning: 
    The clinician agreed with MedGuard's assessment of this issue

    Issue 2:
    Issue Identified by MedGuard: Allopurinol dosing without recent renal function assessment
    Evidence provided by MedGuard: Allopurinol 100 mg twice daily active (Event 2). Latest eGFR 82 mL/min/1.73 m² recorded on 26‑Jan‑2023 (Event 34). >2 years old, making renal dosing uncertain.
    Clinician reasoning: ideally bi-annual monitoring
    The clinician agreed with MedGuard's assessment of this issue

    Issue 3:
    Issue Identified by MedGuard: Simvastatin therapy without recent liver function monitoring
    Evidence provided by MedGuard: Simvastatin 40 mg nightly active (Event 3). Latest liver function tests (ALT, bilirubin, ALP) from 26‑Jan‑2023 were within normal limits (Event 34). No repeat LFTs in >12 months.
    Clinician reasoning: NICE guidance advises annual review
    The clinician agreed with MedGuard's assessment of this issue

    The clinician then considered whether MedGuard correctly identified the flagged issue:

    reasoning: MedGuard identified in Issue 1 the presence of salmeterol (a long‑acting beta‑agonist) being prescribed without any inhaled corticosteroid, which is contraindicated and risks severe asthma exacerbations. This matches the flagged issue. Although MedGuard further mentions the presence of allopurinol and simvastatin, this doesn't distract from the fact that MedGuard has correctly identified the issue at hand.
    correct: true

    The clinician then considered whether MedGuard's intervention would be appropriate for the patient:

    MedGuard believed an intervention was required

    MedGuard's intervention: Immediately discontinue salmeterol and initiate an inhaled corticosteroid (e.g., fluticasone 100 µg BID) or a combined LABA/ICS inhaler (e.g., budesonide/formoterol) as per asthma guidelines; ensure salbutamol remains for rescue. Order repeat renal function (creatinine, eGFR, urate) to review allopurinol dose and adjust if eGFR <30 mL/min. Order repeat liver function tests (ALT, AST, ALP, bilirubin) to confirm safe continuation of simvastatin 40 mg. Document changes and arrange asthma review within two weeks.

    reasoning: The intervention is specific and actionable, it directly resolves the concern of salmeterol being prescribed without any inhaled corticosteroid. It is also directly resolves the concern of allopurinol and simvastatin lacking recent renal and liver function monitoring respectively. This both addresses the flagged issue and is a correct intervention.
    correct: true
</example>

<example>
    Flagged Clinical Issue: Methotrexate prescribed without folic acid

    MedGuard Patient Summary: The patient is a 55‑year‑old woman with active Crohn's disease, liver steatosis, gallbladder calculus, hypertension, a history of falls and light smoking. Current active prescriptions (as of 15 Oct 2021) are oral methotrexate 15 mg weekly (started 1 Oct 2021), a tapering course of prednisolone, calcium chews and rectal Scheriproct preparations. No repeat antihypertensives are listed. Recent investigations (last labs 2 years ago) show normal liver function and eGFR 90 ml/min/1.73 m², but there are no documented liver or renal function tests since methotrexate was re‑started. Methotrexate is a hepatotoxic drug and requires regular monitoring, especially in a patient with known liver steatosis. Additionally, folic acid, which reduces methotrexate toxicity, is not prescribed. These represent significant safety gaps that need prompt correction.

    MedGuard Identified the following issues, all of which were then reviewed by a clinician to assess their correctness:

    Issue 1:
    Issue Identified by MedGuard: Missing liver and renal function monitoring for newly re‑started methotrexate in a patient with known liver steatosis
    Evidence provided by MedGuard: Methotrexate 15 mg weekly started 01 Oct 2021 (Event 2). Liver steatosis recorded on 30 Sep 2021 (Event 11). No liver function or eGFR results documented after 02 Oct 2019 (Event 63).
    Clinician reasoning: 
    The clinician agreed with MedGuard's assessment of this issue

    Issue 2:
    Issue Identified by MedGuard: Absence of folic acid supplementation with methotrexate therapy
    Evidence provided by MedGuard: Methotrexate 15 mg weekly active (Event 2). No folic acid prescription listed among active medications (Events 1‑6).
    Clinician reasoning: 
    The clinician agreed with MedGuard's assessment of this issue

    The clinician then considered whether MedGuard correctly identified the flagged issue:

    reasoning: MedGuard identified the issue in Issue 2
    correct: true

    The clinician then considered whether MedGuard's intervention would be appropriate for the patient:

    MedGuard believed an intervention was required

    MedGuard's intervention: Order same‑day liver function tests (ALT, AST, ALP, GGT, bilirubin) and serum creatinine/eGFR; hold methotrexate until results are available if ALT >2× ULN or eGFR <30 ml/min/1.73 m². Prescribe folic acid 5 mg orally once weekly (taken on a day separate from methotrexate) to start immediately. Arrange regular methotrexate monitoring (LFTs and renal function every 3 months) and document monitoring plan in the record.

    reasoning: In clinical practice, we probably wouldn't withold the methotrexate whilst awaiting bloods as it is necessary for immune management of Crohns and the risk of a potential Crohn's flare would out weigh the need to withold whilst checking LFT/fbc. But practice varies, some clinicians might withold, others would continue, no hard and fast rule so overall i agree. The proposed strategy is correct, perhaps just a little over cautious. I'd probably re-phrase to say "consider" witholding whilst awaiting results but decision should be made on a case by case basis (individualized to risk of flare-up etc)
    correct: true

    Failure mode: 
        - non_critical_omission
</example>

<example>
    Flagged Clinical Issue: Methotrexate prescribed without folic acid

    MedGuard Patient Summary: The 74‑year‑old male has several acute and chronic safety concerns. The most urgent is recent chest pain recorded on 30 April 2023 and 27 April 2023, which warrants immediate cardiac assessment given his ischaemic heart disease, heart valve disease and elevated NT‑proBNP (649 ng/L). He is currently on duplicate anti‑resorptive therapy: weekly alendronic acid (started 06 Jan 2022) and sub‑cutaneous denosumab (Prostap, every 3 months since 30 Dec 2021), increasing risk of oversuppression of bone turnover and osteonecrosis of the jaw. No calcium/vitamin D supplementation is recorded, raising the potential for denosumab‑induced hypocalcaemia. Methotrexate 15 mg weekly (started 31 Jul 2023) is prescribed without documented folic acid prophylaxis. Renal function is stable (eGFR 74‑78 mL/min/1.73 m²) and liver tests are normal, mitigating immediate drug‑disease contraindications. Blood pressure is controlled, but the high NT‑proBNP suggests possible heart failure that is not being treated.

    MedGuard Identified the following issues, all of which were then reviewed by a clinician to assess their correctness:

    Issue 1:
    Issue Identified by MedGuard: Recent chest pain (30 April 2023) in a patient with ischaemic heart disease and elevated NT‑proBNP
    Evidence provided by MedGuard: GP events on 30 April 2023 and 27 April 2023 recorded chest pain; NT‑proBNP 649 ng/L on 29 June 2023; history of ischaemic heart disease and heart valve disease
    Clinician reasoning: Insufficient details though to be able to comment further. It is possible that the chest pain was not cardiac sounding in nature, hence not investigated further (could've been musculoskeletal type pain, highly subjective and requires more detail)
    The clinician agreed with MedGuard's assessment of this issue

    Issue 2:
    Issue Identified by MedGuard: Duplicate anti‑resorptive therapy (alendronic acid + denosumab)
    Evidence provided by MedGuard: Alendronic acid 70 mg weekly repeat medication since 06 Jan 2022; Prostap (denosumab) sub‑cutaneous injection every 3 months repeat medication since 30 Dec 2021
    Clinician reasoning: no indication for both (although i suspect this might not be true combination and might just reflect transition between agents, stopping denosumab and replacing with alendronate) but not enough information to be sure. 
    The clinician agreed with MedGuard's assessment of this issue

    Issue 3:
    Issue Identified by MedGuard: Missing calcium and vitamin D supplementation with denosumab
    Evidence provided by MedGuard: Denosumab ongoing (Prostap) with no recorded calcium or vitamin D supplement; recent serum calcium 2.34 mmol/L (normal but risk present)
    Clinician reasoning: although see above, if transitioning between therapies, this might not be required (it is not mandatory)
    The clinician agreed with MedGuard's assessment of this issue

    Issue 4:
    Issue Identified by MedGuard: Methotrexate prescribed without folic acid prophylaxis
    Evidence provided by MedGuard: Methotrexate 15 mg weekly active from 31 Jul 2023; no folic acid medication listed in active repeat medications
    Clinician reasoning: significant omission
    The clinician agreed with MedGuard's assessment of this issue

    Issue 5:
    Issue Identified by MedGuard: Possible untreated heart failure (elevated NT‑proBNP, dyspnoea)
    Evidence provided by MedGuard: NT‑proBNP 649 ng/L on 29 June 2023; dyspnoea noted on 22 May 2023; no cardiac medications recorded
    Clinician reasoning: Not enough clinical information to be confident this is heart failure, anything up to 2000ng/L is considered only "possible" heart failure and he needs further investigation before recommending further therapies. 
    The clinician disagreed with MedGuard's assessment of this issue

    The clinician then considered whether MedGuard correctly identified the flagged issue:

    reasoning: MedGuard identified the issue in Issue 4
    correct: true

    The clinician then considered whether MedGuard's intervention would be appropriate for the patient:

    MedGuard believed an intervention was required

    MedGuard's intervention: Arrange urgent cardiac assessment (ECG, troponin and possible admission) for the chest pain reported on 30 April 2023; Stop alendronic acid immediately to avoid duplicate anti‑resorptive therapy with denosumab; Initiate calcium 500 mg + vitamin D 800 IU daily supplementation; Add folic acid 5 mg weekly to methotrexate regimen; Refer to heart failure clinic for evaluation and consider initiating guideline‑directed therapy (e.g., ACE inhibitor or diuretic) based on clinical assessment.

    reasoning: Re issue 1: needs more clinical context before recommending emergency evaluation 
    Re issue 5, the NT pro BNP is only slightly elevated, he'd need an echo for confirmation, i wouldn't say he would qualify for heart failure clinic at this stage, he'd need further tests. Up to 2000ng/L is "possible" heart failure . Echo - if felt to be warranted. I note advanced metastatic prostate cancer, it may be that further investigation is not warranted at this time of life. 
    correct: true

    Failure mode: 
        - non_critical_omission
</example>

<example>
    Flagged Clinical Issue: Prescription of an NSAID, without co-prescription of an ulcer-healing drug, to a patient with a history of peptic ulceration

    MedGuard Patient Summary: The patient is a 54‑year‑old male with recorded hypertension, COPD/asthma, ischaemic heart disease, and a past peptic ulcer. Recent clinical entries (e.g., 04 Apr 2023 BP 133/85, 15 Jun 2021 BP 161/80, 28 Apr 2022 BP 158/86) show persistently elevated blood pressures, indicating uncontrolled hypertension. The most recent medication record shows the patient is still taking ibuprofen 200 mg three times daily (event 1) despite a documented history of peptic ulcer (frailty deficit). No gastro‑protective agent is prescribed. There is also no current inhaled therapy for his chronic respiratory disease; the last recorded inhalers (Fostair, Salbutamol, Beclometasone/Formoterol) all have end dates before the SMR and are flagged as not being taken. The combination of untreated hypertension, lack of COPD/asthma treatment, and ongoing NSAID use in a ulcer‑prone patient represents significant safety and therapeutic gaps that require immediate action.

    MedGuard Identified the following issues, all of which were then reviewed by a trained clinician to assess their correctness:

    Issue 1:
    Issue Identified by MedGuard: Ibuprofen use in a patient with a history of peptic ulcer
    Evidence provided by MedGuard: Event 1 records ibuprofen 200 mg tablets taken three times daily (course started 16 Aug 2023) and the frailty deficits list a peptic ulcer; no proton‑pump inhibitor or other gastro‑protection is prescribed.
    Clinician reasoning: 
    The clinician agreed with MedGuard's assessment of this issue

    Issue 2:
    Issue Identified by MedGuard: Uncontrolled hypertension with no antihypertensive medication prescribed
    Evidence provided by MedGuard: Multiple blood pressure readings show systolic values >150 mmHg (e.g., 15 Jun 2021: 161/80; 28 Apr 2022: 158/86; 04 Apr 2023: 133/85) and the patient is on the hypertension register, yet no repeat antihypertensive medication appears in the current medication list.
    Clinician reasoning: 
    The clinician agreed with MedGuard's assessment of this issue

    Issue 3:
    Issue Identified by MedGuard: Absent inhaled therapy for documented COPD/asthma
    Evidence provided by MedGuard: The patient has a COPD/asthma diagnosis (frailty deficits, events 98, 177, 178) and recent symptoms (suspected COPD on 15 Mar 2023). The last inhaler prescriptions (Fostair, Salbutamol, Beclometasone/Formoterol) all ended before the SMR and are flagged as not being taken.
    Clinician reasoning: 
    The clinician agreed with MedGuard's assessment of this issue

    The clinician then considered whether MedGuard correctly identified the flagged issue: Prescription of an NSAID, without co-prescription of an ulcer-healing drug, to a patient with a history of peptic ulceration

    They concluded that MedGuard did correctly identify the flagged issue

    The clinician then considered whether MedGuard's intervention would be appropriate for the patient: 1. Discontinue ibuprofen immediately; prescribe paracetamol for analgesia and start a proton‑pump inhibitor (e.g., omeprazole 20 mg daily) for ulcer protection. 2. Initiate antihypertensive therapy – for example, start ramipril 2.5 mg daily (titrate to target BP <140/90) or an alternative guideline‑based agent after assessing renal function and electrolytes. 3. Restart appropriate inhaled treatment for COPD/asthma: prescribe beclometasone 100 µg/formoterol 6 µg inhaler, two actuations twice daily, and a short‑acting rescue inhaler (salbutamol 100 µg) as needed, with a review of inhaler technique at the next visit.

    MedGuard believed an intervention was required: True

    MedGuard's intervention: 1. Discontinue ibuprofen immediately; prescribe paracetamol for analgesia and start a proton‑pump inhibitor (e.g., omeprazole 20 mg daily) for ulcer protection. 2. Initiate antihypertensive therapy – for example, start ramipril 2.5 mg daily (titrate to target BP <140/90) or an alternative guideline‑based agent after assessing renal function and electrolytes. 3. Restart appropriate inhaled treatment for COPD/asthma: prescribe beclometasone 100 µg/formoterol 6 µg inhaler, two actuations twice daily, and a short‑acting rescue inhaler (salbutamol 100 µg) as needed, with a review of inhaler technique at the next visit.

    reasoning: 1. it is illogical to stop the iburpofen and start a gastroprotective agent at the same time. By stopping we remove the risk factor so PPI not required. I'd also want to know exactly how long ago the ulcer was to inform decision making. 
    2. reasonable to want to treat, i would add involve patient in decision making. I'd probably want home readings first (or 24hour BP monitor)
    3. agree
    correct: true

    failure_mode:
    - reasoning_error

    [n.b. note how the intervention is marked as correct, because it addresses the flagged issue, even if the reasoning has identified issues with some other parts of the intervention]
</example>

<example>
    Flagged Clinical Issue: Prescription of diltiazem or verapamil in a patient with heart failure

    MedGuard Patient Summary: The 72‑year‑old male is on nine chronic medications. Recent labs show a stable renal function (eGFR 67‑85 mL/min/1.73m²) and a borderline high digoxin level (0.97 µg/L in Feb 2025, 1.17 µg/L in Nov 2023). He has atrial fibrillation, heart failure with reduced LVEF, hypertension, gout, and obesity (BMI≈34). Significant safety concerns are identified: (1) Citalopram 40 mg daily exceeds the recommended maximum of 20 mg in patients over 65, increasing QT‑prolongation risk, especially when combined with verapamil. (2) Verapamil 240 mg modified‑release is prescribed twice daily – a dosing regimen not approved and results in excess plasma concentrations. Verapamil also markedly raises digoxin levels and, via CYP3A4 inhibition, raises colchicine concentrations, creating a risk of digoxin toxicity, AV‑block, and colchicine myopathy. (3) The digoxin level is already at the upper end of the therapeutic range and may rise further while verapamil is continued. (4) Colchicine 500 µg four times daily is appropriate for gout flares but, in the presence of verapamil, poses a risk of toxicity. These issues warrant immediate medication changes and targeted monitoring. Other medications (omeprazole, perindopril, dabigatran, atorvastatin, allopurinol) appear appropriate given current labs and clinical status.

    MedGuard Identified the following issues, all of which were then reviewed by a trained clinician to assess their correctness:

    Issue 1:
    Issue Identified by MedGuard: Citalopram dose 40 mg exceeds age‑related limit, increasing QT‑prolongation risk
    Evidence provided by MedGuard: Patient age 72; current prescription Citalopram 40 mg daily (Event 3). Guidelines advise ≤20 mg daily in patients >65 due to ventricular arrhythmia risk.
    Clinician reasoning: 
    The clinician agreed with MedGuard's assessment of this issue

    Issue 2:
    Issue Identified by MedGuard: Verapamil 240 mg MR prescribed twice daily – excessive dosing and contraindicated with digoxin
    Evidence provided by MedGuard: Verapamil 240 mg modified‑release tablets, dosage "ONE TO BE TAKEN TWICE A DAY" (Event 8). Verapamil MR is intended for once‑daily dosing; also interacts with digoxin, raising serum levels (digoxin 0.97 µg/L, Event 18).
    Clinician reasoning: Partially correct.
    verapamil can be given twice daily with a total daily dose up to 480mg 
    if combined with digoxin requires close monitoring (not an absolute contraindication to co-prescribe) Also hasn't mentioned issue with heart failure.
    The clinician disagreed with MedGuard's assessment of this issue

    Issue 3:
    Issue Identified by MedGuard: Potential colchicine toxicity due to concomitant CYP3A4‑inhibiting verapamil
    Evidence provided by MedGuard: Colchicine 500 µg QID (Event 9) together with verapamil MR BID (Event 8). Verapamil is a moderate CYP3A4 inhibitor, increasing colchicine plasma concentrations and risk of myopathy.
    Clinician reasoning: agree would reduce dose to BD
    The clinician agreed with MedGuard's assessment of this issue

    Issue 4:
    Issue Identified by MedGuard: Borderline high digoxin level (0.97‑1.17 µg/L) with interacting verapamil raises risk of digoxin toxicity
    Evidence provided by MedGuard: Serum digoxin level 0.970 µg/L (Event 18, 24‑May‑2025) and 1.170 µg/L (Event 105, 03‑Nov‑2023). Verapamil increases digoxin levels; patient heart rate 60‑73 bpm.
    Clinician reasoning: 
    The clinician agreed with MedGuard's assessment of this issue

    The clinician then considered whether MedGuard correctly identified the flagged issue: Prescription of diltiazem or verapamil in a patient with heart failure

    They concluded that MedGuard did correctly identify the flagged issue

    The clinician then considered whether MedGuard's intervention would be appropriate for the patient: 1. Stop verapamil immediately and arrange cardiology review for alternative rate‑control (e.g., consider low‑dose beta‑blocker or adjust digoxin dose). 2. Reduce citalopram to 20 mg daily (or switch to an antidepressant without QT risk) and repeat ECG after dose change. 3. Repeat serum digoxin level in 7‑10 days after verapamil cessation and adjust digoxin dose if level remains >0.9 µg/L. 4. Maintain colchicine regimen but monitor for signs of toxicity now that verapamil is stopped.

    MedGuard believed an intervention was required: True

    MedGuard's intervention: 1. Stop verapamil immediately and arrange cardiology review for alternative rate‑control (e.g., consider low‑dose beta‑blocker or adjust digoxin dose). 2. Reduce citalopram to 20 mg daily (or switch to an antidepressant without QT risk) and repeat ECG after dose change. 3. Repeat serum digoxin level in 7‑10 days after verapamil cessation and adjust digoxin dose if level remains >0.9 µg/L. 4. Maintain colchicine regimen but monitor for signs of toxicity now that verapamil is stopped.

    reasoning: 1. Avoid abrupt discontinuation as he has AF and might develop fast ventricular response leading to hospitalization. Seek cardiology opinion first and review any cardio letters
    2. Review symptoms first before reduce
    3. agree
    4. i would reduce to BD in interim until AF control strategy organised. 
    Although this intervention addresses the flagged issue, and therefore is marked as correct, I am concerned about abrupt cessation in someone with AF - review cardiology letters and liase with specialist before making change. He may have a history of difficult to control AF
    correct: true

    Failure mode: knowledge_gap
</example>"""
