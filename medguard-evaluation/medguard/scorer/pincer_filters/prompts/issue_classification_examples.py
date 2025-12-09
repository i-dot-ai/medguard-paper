# The following examples are initially taken from the train dataset to align the scoring with the clinician's reasoning for issue classification.
# Examples have been adjusted to evenly sample from positive and negative cases.

ISSUE_CLASSIFICATION_EXAMPLES = """
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
</example>

<example>
    MedGuard Patient Summary: The patient is a 65-year-old male with asthma, peptic ulcer history and recent prescriptions for salmeterol, allopurinol, simvastatin, salbutamol, montelukast and lansoprazole. The patient is being prescribed salmeterol (a long‑acting beta‑agonist) without any inhaled corticosteroid. Additionally, both allopurinol and simvastatin lack recent renal and liver function monitoring respectively; the latest eGFR and LFTs are over two years old, making dose assessment uncertain. No other acute events or critical drug‑drug interactions are evident.

    Flagged Clinical Issue: 7 - Prescription of a long-acting beta-2 agonist inhaler to a patient with asthma who is not also prescribed an inhaled corticosteroid

    MedGuard Identified the following issues, all of which were then reviewed by a clinician to assess their correctness:

    Issue 1:
    Issue Identified by MedGuard: Allopurinol dosing without recent renal function assessment
    Evidence provided by MedGuard: Allopurinol 100 mg twice daily active. Latest eGFR 82 mL/min/1.73 m² >2 years old, making renal dosing uncertain.
    Clinician reasoning: ideally bi-annual monitoring
    The clinician agreed with MedGuard's assessment of this issue

    Issue 2:
    Issue Identified by MedGuard: Simvastatin therapy without recent liver function monitoring
    Evidence provided by MedGuard: Simvastatin 40 mg nightly active. Latest liver function tests (ALT, bilirubin, ALP) were within normal limits. No repeat LFTs in >12 months.
    Clinician reasoning: NICE guidance advises annual review
    The clinician agreed with MedGuard's assessment of this issue

    The clinician then assessed whether MedGuard correctly identified the flagged clinical issue or not:

    reasoning: Although MedGuard made reference to the flagged issue in their patient summary, this is not called out as an issue and therefore MedGuard was mistaken in not calling this out.
    correct: false
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
</example>
"""
