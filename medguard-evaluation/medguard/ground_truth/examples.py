from textwrap import dedent
from medguard.ground_truth.models import GroundTruthAssessment

examples = [
    (
        dedent("""
        **Issue 1**
        issue: No inhaled corticosteroid for persistent asthma despite ongoing symptoms and documented non‑adherence to inhaled steroids.
        evidence: Asthma annual review (27‑Dec‑2024) recorded "Not using inhaled steroids" and "Asthma treatment compliance unsatisfactory" with ACT score 21 and reported dyspnoea.
        intervention required: True

        clinician agrees with issue: True
        clinician reasoning: however it appears this is due to non-compliance so there isn't much anyone can do if she doesn't comply with guideline indicated therapy

        **Issue 2**
        issue: Absence of antiplatelet therapy for secondary prevention of coronary heart disease.
        evidence: Aspirin 75 mg was discontinued on 23‑Apr‑2024 (Event 33) and is not listed as a current repeat medication; patient has documented CHD (CHD_REG_V45, cardiac clinic visits, prior MI).
        intervention required: True

        clinician agrees with issue: True
        clinician reasoning: Technically correct given her comorbidities HOWEVER aspirin is risky and i suspect appropriately discontinued, i assume risked outweighed benefit so it was stopped

        **Issue 3**
        issue: Absence of high‑intensity statin therapy for secondary prevention of coronary heart disease.
        evidence: Atorvastatin 80 mg was stopped on 23‑Apr‑2024 (Event 32) and is not being prescribed currently; patient has CHD and dyslipidaemia (LDL not recorded but prior lipid panel shows total cholesterol 3.5 mmol/L, HDL 1.78 mmol/L).
        intervention required: True

        clinician agrees with issue: False
        clinician reasoning: I'm going to say incorrect because at this degree of frailty, i think it is the right decision to discontinue, she's had many years of statin therapy already

        **Issue 4**
        issue: Absence of ACE‑inhibitor therapy for hypertension, CKD protection and cardiovascular risk reduction.
        evidence: Ramipril 2.5 mg was stopped on 23‑Apr‑2024 (Event 30) and no other antihypertensive is active; recent BP 124/68 mmHg but prior readings show systolic up to 147 mmHg.
        intervention required: True

        clinician agrees with issue: False
        clinician reasoning: Not technically incorrect however with advanced frailty, i suspect risk outweighs benefit so these were appropriately deprescribed, 

        **Intervention**
        intervention required: True
        intervention: 1. Prescribe an inhaled corticosteroid (e.g., beclometasone 100 µg inhaler, 2 puffs twice daily) and arrange a focused asthma education session to improve adherence.\n2. Restart low‑dose aspirin 75 mg once daily for secondary prevention of CHD, unless a contraindication (e.g., active bleed) is identified.\n3. Restart atorvastatin 40 mg once daily (or 20 mg if tolerance is a concern) for secondary prevention of CHD; monitor liver function and CKD parameters after 4‑6 weeks.\n4. Restart ramipril 2.5 mg once daily, titrating up as tolerated, to control blood pressure, provide renal protection, and reduce cardiovascular risk; re‑check serum creatinine and potassium in 2 weeks.
        clinician agrees with the intervention: no
        clinician reasoning: i don't think all these preventative medicines suggestion are appropriate at advanced age and frailty. However i would say there is nothing technically inaccurate about the suggestions, they are just not clinically appropriate in the context of advanced frailty.
        intervention should be: I think this has been an appropriate deprescribing decision towards end of life. I think the suggestions made here are correct for someone younger and fitter. Ultimately, more information about the patient preferences and functional abilitiies would be helpful for decision making here.
    """),
        GroundTruthAssessment(
            reasoning="The initial assessment was very thorough though overly cautious on flagging lots of issues that are not a concern with a patient of their age and frailty. It's worth including these as a note, but these should not be recorded as issues because they do not require an intervention.",
            issues=[
                "No inhaled corticosteroid for persistent asthma despite ongoing symptoms and documented non-adherence to inhaled steroids.",
            ],
            intervention=[],
            notes=[
                "The lack of an inhaled corticosteroid is a valid concern. However, the patient is non-compliant with their current medication and it is not clear that this would be effective.",
                "The absence of antiplatelet therapy for secondary prevention of coronary heart disease is a valid concern. However in this case the risk of bleeding outweighs the benefit of therapy and so the decision to discontinue was appropriate.",
                "The absence of a statin is a valid concern although the decision to discontinue is correct. This is because the patient has had many years of statin therapy already.",
                "The absence of an ACE inhibitor is a valid concern. However, the patient has advanced frailty and so the risk of side effects outweighs the benefit of therapy that would come from restarting it.",
            ],
        ),
    ),
    (
        dedent("""
        **Intervention**
        intervention required: False
        intervention: 
        clinician agrees with the intervention: yes
    """),
        GroundTruthAssessment(
            reasoning="The initial assessment indicated that the patient did not have any issues and that no intervention was required. The clinician agrees with this assessment.",
            issues=[],
            intervention=[],
            notes=[],
        ),
    ),
    (
        dedent("""
        **Issue 1**
        issue: Renal function not monitored recently, risking inappropriate apixaban dosing
        evidence: Last recorded serum creatinine 94 µmol/L, eGFR 67 mL/min/1.73 m² (CrCl 63 mL/min) from laboratory results dated 45 (August 2022). No newer renal function test is documented up to the SMR date 25 March 2024.
        intervention required: True

        clinician agrees with issue: True
        clinician reasoning: however patient is at end of life, i'd question whether invasive tests are in best interests and i could live with the slightly increased risk of not knowing. I'd also accept stopping anticoag entirely if patient was in agreement with increased risk of stroke but reduced risk of major bleed

        The initial assessment also missed the following issues: statin in patient on palliative care register with advanced care of the dying plan - probably not indicated

        **Intervention**
        intervention required: True
        intervention: Order serum creatinine, urea and calculate eGFR/CrCl within the next two weeks. If eGFR falls <30 mL/min/1.73 m² (or CrCl <30 mL/min), reduce apixaban to 2.5 mg twice daily per dose‑adjustment guidelines; otherwise continue current dose and repeat renal monitoring annually.
        clinician agrees with the intervention: yes
    """),
        GroundTruthAssessment(
            reasoning="The clinician agrees with the initial assessment, although they noted that it missed an issue (the statin) which has now been included. The clinician agreed with the intervention so this was left unchanged.",
            issues=[
                "Renal function not monitored recently, risking inappropriate apixaban dosing",
                "Statin in patient on palliative care register with advanced care of the dying plan - probably not indicated",
            ],
            intervention=[
                "Order serum creatinine, urea and calculate eGFR/CrCl within the next two weeks.",
                "If eGFR falls <30 mL/min/1.73 m² (or CrCl <30 mL/min), reduce apixaban to 2.5 mg twice daily per dose‑adjustment guidelines.",
            ],
            notes=[
                "The patient is at end of life and so the risk of invasive testing outweighs the benefit of knowing the patient's renal function.",
            ],
        ),
    ),
    (
        dedent("""
        **Issue 1**
        issue: Duplicate/overdose of furosemide leading to excessive loop diuretic exposure
        evidence: Two active repeat prescriptions: Event 1 (40 mg tablets, 2 × morning and 2 × lunchtime) and Event 5 (40 mg tablet, 80 mg morning and 40 mg lunchtime). Both are currently repeat medications, giving a combined daily dose of 120–160 mg.
        intervention required: True

        clinician agrees with issue: True
        clinician reasoning: The intended total daily dose is confusing here i agree. 

        **Issue 2**
        issue: Uncontrolled hypertension despite amlodipine 5 mg
        evidence: Multiple recent BP readings: 173/107 mmHg and 175/104 mmHg (Event 193‑194), 168/85 mmHg (Event 206), 160/80 mmHg (Event 224), and 110/86 mmHg (Event 25) showing persistent systolic >160 mmHg.
        intervention required: True

        clinician agrees with issue: True

        **Issue 3**
        issue: High dose gabapentin contributing to fall risk in a frail elderly patient
        evidence: Active repeat gabapentin 600 mg three times daily (Event 13) together with frailty deficits (falls, gait problems) recorded in the frailty profile.
        intervention required: True

        clinician agrees with issue: True

        **Intervention**
        intervention required: True
        intervention: 1. Discontinue the duplicate furosemide prescription and reduce the total daily dose to 80 mg (e.g., 40 mg twice daily) to avoid over‑diuresis. 2. Initiate an ACE inhibitor such as ramipril 2.5 mg once daily (titrating to target) to achieve blood pressure control and provide renal protection. 3. Reduce gabapentin to 300 mg three times daily (total 900 mg/day) and arrange a review of neuropathic pain control with monitoring for dizziness or falls.
        clinician agrees with the intervention: yes
    """),
        GroundTruthAssessment(
            reasoning="The clinician agreed with all the issues and intervention, so these were copied unchanged. The clinician's note on the first issue was added to the intervention as a note.",
            issues=[
                "Duplicate/overdose of furosemide leading to excessive loop diuretic exposure",
                "Uncontrolled hypertension despite amlodipine 5 mg",
                "High dose gabapentin contributing to fall risk in a frail elderly patient",
            ],
            intervention=[
                "Discontinue the duplicate furosemide prescription and reduce the total daily dose to 80 mg (e.g., 40 mg twice daily)",
                "Initiate an ACE inhibitor such as ramipril 2.5 mg once daily",
                "Reduce gabapentin to 300 mg three times daily (total 900 mg/day)",
            ],
            notes=[
                "The intended daily dose of furosemide is confusing for this patient given they have two active repeat prescriptions.",
            ],
        ),
    ),
    (
        dedent("""
        **Intervention**
        intervention required: False
        intervention: 
        clinician agrees with the intervention: yes
    """),
        GroundTruthAssessment(
            reasoning="The initial assessment indicated that the patient did not have any issues and that no intervention was required. The clinician agrees with this assessment.",
            issues=[],
            intervention=[],
            notes=[],
        ),
    ),
    (
        dedent("""
        **Issue 1**
        issue: Metformin prescribed despite severe renal impairment (eGFR 14 mL/min/1.73m²)
        evidence: eGFR 14 mL/min/1.73m² recorded on 03 Jan 2024 (Event 57) while metformin 500 mg BID has been continued from 20 Sep 2024 (Event 4).
        intervention required: True

        clinician agrees with issue: False
        clinician reasoning: eGFR is 35 so the dose of metformin is ok

        **Issue 2**
        issue: Atenolol 100 mg contributing to symptomatic hypotension in the context of low BP and poly‑pharmacy with amlodipine and tamsulosin
        evidence: Blood pressure readings of 93/61 mmHg (09 Feb 2024, Event 29) and 97/53 mmHg (02 Jan 2024, Event 59) while on atenolol 100 mg daily (Event 3), amlodipine 5 mg daily (Event 7) and tamsulosin 400 µg daily (Event 2).
        intervention required: True

        clinician agrees with issue: True

        **Issue 3**
        issue: Allopurinol dose too high for stage 5 CKD (300 mg daily)
        evidence: Allopurinol 300 mg daily ongoing (Event 5) with eGFR 14 mL/min/1.73m² (Event 57). Guidelines recommend dose ≤100 mg daily when eGFR < 30.
        intervention required: True

        clinician agrees with issue: False
        clinician reasoning: eGFR is 35

        **Intervention**
        intervention required: True
        intervention: 1. Discontinue metformin immediately. 2. Stop atenolol 100 mg and reassess blood pressure; consider titrating amlodipine to the lowest effective dose or alternative antihypertensive if needed. 3. Reduce allopurinol to 100 mg daily (or stop if urate level not target) and arrange urate monitoring. Re‑check serum potassium and renal function within 1 week after changes.
        clinician agrees with the intervention: no
        clinician reasoning: eGFR is 35 so the dose adjustments are needed
        intervention should be: agree consider reducing atenolol dose depending on response
    """),
        GroundTruthAssessment(
            reasoning="The clinician disagreed with the initial assessment given the patient's eGFR. Hence these issues were removed. The intervention was also updated to reflect the clinician's feedback. The recommendation to consider reducing the atenolol dose was part of the 2nd intervention, so has been included with that intervention. In addition, the suggestion to titrate amlodipine was moved to a note as it was a conditional intervention.",
            issues=[
                "Atenolol 100 mg contributing to symptomatic hypotension in the context of low BP and poly‑pharmacy with amlodipine and tamsulosin",
            ],
            intervention=["Stop atenolol 100mg and reassess blood pressure."],
            notes=[
                "The eGFR is 35 so the dose of metformin is appropriate.",
                "Consider titrating amlodipine to the lowest effective dose or alternative antihypertensive if needed.",
            ],
        ),
    ),
    (
        dedent("""
        **Issue 1**
        issue: No recent liver function monitoring for methotrexate therapy
        evidence: Methotrexate restarted 26 Oct 2020 (Event 8); last LFT performed 25 Oct 2019 (Event 40) before restart, with no subsequent LFTs recorded.
        intervention required: False

        clinician agrees with issue: True

        **Issue 2**
        issue: Concurrent use of two high‑potency topical corticosteroids increasing risk of skin atrophy
        evidence: Both betamethasone valerate 0.1% cream (Event 4) and betamethasone 0.1%/fusidic acid 2% cream (Event 5) are listed as repeat medications at the time of the SMR.
        intervention required: True

        clinician agrees with issue: True

        **Issue 3**
        issue: Potential statin‑calcium channel blocker interaction (atorvastatin with amlodipine) elevating risk of myopathy
        evidence: Atorvastatin 20 mg daily (Event 3) and amlodipine 10 mg daily (Event 1) are both active; amlodipine can increase atorvastatin plasma concentrations via CYP3A4 inhibition.
        intervention required: False

        clinician agrees with issue: False
        clinician reasoning: they are both low dose, i wouldn't be concerned, risk is higher with simvastatin or high dose atorvastatin, neither apply here. 

        **Intervention**
        intervention required: True
        intervention: Discontinue the betamethasone valerate 0.1% cream and continue only the betamethasone 0.1%/fusidic acid 2% cream; arrange a follow‑up skin assessment in two weeks to ensure disease control and monitor for any signs of steroid‑induced skin atrophy.
        clinician agrees with the intervention: partial
        clinician reasoning: didn't suggest LFT monitoring give recent re-starting of methotrexate
        intervention should be: check bloods 3monthly on methotrexate
    """),
        GroundTruthAssessment(
            reasoning="The clinician agreed with the first two issues, but disagreed with the third. They also didn't suggest any missued issues. Notably the first issue did not require an intervention, so this was copied across to the notes. The second issue was copied across to the issues, and the third issue was removed. Their feedback on the intervention led to an update to the intervention to include the 3 monthly bloods which the clinician explicitly stated was required, and therefore is included as an intervention.",
            issues=[
                "Concurrent use of two high‑potency topical corticosteroids increasing risk of skin atrophy",
            ],
            intervention=[
                "Discontinue the betamethasone valerate 0.1% cream and continue only the betamethasone 0.1%/fusidic acid 2% cream",
                "Arrange a follow‑up skin assessment in two weeks to ensure disease control and monitor for any signs of steroid‑induced skin atrophy.",
                "Check bloods every 3 months while on methotrexate",
            ],
            notes=[
                "No recent liver function monitoring for methotrexate therapy",
                "Although the patient is on both atorvastatin and amlodipine, the dose of both is low and there is little risk of interaction.",
            ],
        ),
    ),
    (
        dedent("""
        **Issue 1**
        issue: Uncontrolled hypertension (164/82 mmHg) on enalapril 5 mg monotherapy
        evidence: Blood pressure recorded on 22 Feb 2023: systolic 164 mmHg, diastolic 82 mmHg; current medication list shows only enalapril 5 mg daily (started 2004).
        intervention required: True

        clinician agrees with issue: False
        clinician reasoning: i'd accept approx 160/80 in advanced age and frailty

        **Issue 2**
        issue: Absence of antiplatelet therapy for secondary prevention of coronary artery disease and peripheral arterial disease
        evidence: CHD and PAD recorded on multiple QOF registers and clinical entries (e.g., 22 Feb 2023 CHD annual review, PAD register). No current antiplatelet medication; aspirin 75 mg was stopped on 27 Sep 2020 (Event 80).
        intervention required: True

        clinician agrees with issue: False
        clinician reasoning: appears to have been appropriately deprescribed in view of risk outweighing benefit

        **Issue 3**
        issue: High dose mirtazapine (30 mg) contributing to fall risk in a frail, housebound patient
        evidence: Mirtazapine 30 mg nightly active since 15 Aug 2017 (Event 3). Documented fall on 18 Sep 2020 (Event 97) and frailty deficits include falls, mobility problems, and housebound status.
        intervention required: True

        clinician agrees with issue: True

        **Issue 4**
        issue: Long‑term proton‑pump inhibitor use (>10 years) without documented GI indication
        evidence: Lansoprazole 15 mg daily continuously since 27 Jul 2011 (Event 1); no current ulcer disease or NSAID use noted.
        intervention required: False

        clinician agrees with issue: True
        clinician reasoning: although i would recommend an intervention to deprescribe

        The initial assessment also missed the following issues: deprescribe unnecessary PPI

        **Intervention**
        intervention required: True
        intervention: 1. Add low‑dose aspirin 75 mg once daily for secondary cardiovascular prevention (unless contraindicated). 2. Intensify blood pressure control: either increase enalapril to 10 mg daily and add a thiazide diuretic (e.g., hydrochlorothiazide 12.5 mg once daily) or switch to a combination ACE‑inhibitor/CCB regimen. 3. Reduce mirtazapine to 15 mg nightly (or consider tapering and switching to a non‑sedating antidepressant) to lower sedation‑related fall risk. Re‑assess blood pressure and fall frequency in 4–6 weeks after changes.
        clinician agrees with the intervention: partial
        clinician reasoning: in view of advanced age and frailty, personalise BP target 160/80 probably acceptable
        i think aspirin appropriately deprescribed risk > benefit
        agree not unreasonable to reduce dose mirtazapine
        intervention should be: desprescribe PPI - not indicated
    """),
        GroundTruthAssessment(
            reasoning="The clinician disagreed with several issues, which were reflected or added as notes. The final two issues were added to the issues, and reflected in the updated intervention.",
            issues=[
                "High dose mirtazapine (30mg) contributing to fall risk in a frail, housebound patient",
                "Unnecessary proton-pump inhibitor should be deprescribed given no documented indication",
            ],
            intervention=[
                "Reduce mirtazapine to 15 mg nightly (or consider tapering and switching to a non‑sedating antidepressant)."
                "Re‑assess blood pressure and fall frequency in 4–6 weeks after changes.",
                "Deprescribe unnecessary proton-pump inhibitor",
            ],
            notes=[
                "The patient has a high blood pressure of 164/82 mmHg. Given their advanced age and frailty this is an acceptable risk.",
                "The patient has recently been deprescribed from aspirin 75mg, although this decision was taken in view of the full risk/benefit profile and was appropriate.",
            ],
        ),
    ),
    (
        dedent("""
        **Issue 1**
        issue: Inappropriate chronic use of codeine for ongoing low back pain, posing risk of opioid dependence and adverse effects
        evidence: Event 1 shows Codeine 30 mg tablets prescribed on 13 Jun 2023 and recorded as being taken at the SMR (08 Feb 2024). Historical records (Events 22, 90, 117, 129, etc.) document multiple long‑term codeine courses spanning 2019‑2023, indicating substantial cumulative exposure. Current weight/BMI of 160 kg (BMI 58.8) recorded on 01 Mar 2024 increases risk of opioid‑related respiratory depression.
        intervention required: True

        clinician agrees with issue: True

        The initial assessment also missed the following issues: although comments on obesity related VTE risk with contraceptive patch, doesn't recommend counselling for alternative (she is >35, very obese) as she has high risk of failure 

        **Intervention**
        intervention required: True
        intervention: Discontinue codeine immediately. Arrange a same‑day referral to the multidisciplinary pain team for assessment and initiation of an evidence‑based pain management plan (e.g., physiotherapy, NSAID if not contraindicated, or alternative non‑opioid analgesics). Provide the patient with information on opioid withdrawal symptoms and arrange a follow‑up appointment within 1 week to assess pain control and manage withdrawal if needed.
        clinician agrees with the intervention: no
        clinician reasoning: Unfortunately, pain team waiting lists range from 12-18m. Abrupt discontinuation of opioid will cause withdrawal and unlikely to be effective without extensive support and education.
        intervention should be: sexual health/contraceptive counselling re alternative contraception 
    """),
        GroundTruthAssessment(
            reasoning="The clinician agreed with the first issue, and mentioned that there was an issue which was also missed. Both of these were added as issues. In addition, the clinician's feedback on the intervention was included in the updated intervention with the codeine discontinuation removed from the intervention and added instead as a note. Although the intervention is advice based, because the clinician explicitly stated this it's therefore included.",
            issues=[
                "Inappropriate chronic use of codeine for ongoing low back pain, posing risk of opioid dependence and adverse effects",
                "Venous thromboembolism risk associated with contraceptive patch use in very obese patient.",
            ],
            intervention=[
                "Sexual health or contraceptive counselling about alternative contraception."
            ],
            notes=[
                "The patient is at risk of inappropriate chronic use of codeine for ongoing low back pain, posing risk of opioid dependence and adverse effects. However pain team waiting lists range from 12-18m and so abrupt discontinuation of opioid will cause withdrawal. It is unlikely to be effective without extensive support and education.",
            ],
        ),
    ),
    (
        dedent("""
        **Issue 1**
        issue: Concurrent use of two nitrate preparations (sublingual GTN spray and nitroglycerin transdermal patch) in a patient with low blood pressure
        evidence: GTN spray prescribed 28 Feb 2025 (Event 3); nitroglycerin patch (Matrifen) prescribed 28 May 2025 (Event 18); blood pressure 98/68 mmHg on 24 Mar 2025 (Event 47) and home reading 125/75 mmHg on 5 May 2025 (Event 45)
        intervention required: True

        clinician agrees with issue: True
        clinician reasoning: although GTN spray only lowers BP transiently, i wouldn't be too concerned

        **Issue 2**
        issue: Combined aspirin 75 mg daily with apixaban 5 mg BID increases bleeding risk, especially with current hematuria and indwelling catheter
        evidence: Aspirin 75 mg daily (Event 7); apixaban 5 mg BID started 5 Jun 2025 (Event 15); urine dipstick shows hematuria +++ and protein +++ on 23 Jun 2025 (Event 22); indwelling urethral catheter noted (Event 22)
        intervention required: True

        clinician agrees with issue: True

        **Issue 3**
        issue: Co‑prescription of amitriptyline 100 mg nightly with sertraline 100 mg daily raises risk of serotonin syndrome and adds anticholinergic burden contributing to falls
        evidence: Amitriptyline 100 mg nightly (Event 6); sertraline 100 mg daily (Event 9); frailty deficits include falls, hypotension/syncope (listed in frailty profile); patient's age 69
        intervention required: True

        clinician agrees with issue: True

        **Intervention**
        intervention required: True
        intervention: 1. Discontinue aspirin 75 mg daily and document that bleeding risk outweighs secondary CHD benefit while the patient is on therapeutic apixaban for recent pulmonary embolism. 2. Stop the sublingual GTN spray; retain the nitroglycerin transdermal patch for chronic angina prophylaxis and advise the patient to avoid any nitrate use within 24 hours of patch removal. 3. Cease amitriptyline 100 mg nightly; continue sertraline for depression/anxiety and arrange a review of mood and sleep symptoms. Follow up: repeat urine dipstick in 1 week to ensure resolution of hematuria, monitor blood pressure after nitrate change, and reassess depressive symptoms in 4 weeks.
        clinician agrees with the intervention: partial
        clinician reasoning: 1. agree
        2. i think this is unnecessary, the impact on BP from SL nitrates is transient
        3. easier said than done without alternative, i'd advise gradual taper

        
        intervention should be: gradual taper of amitriptyline needed, avoid abrupt discontinuation
    """),
        GroundTruthAssessment(
            reasoning="The clinician agreed with all the issues, but later noted in the intervention that they disagreed with the first issue. Hence this was not included as an issue but added instead as a note. The interventions recommending documentation have been included as notes rather than interventions.",
            issues=[
                "Combined aspirin 75 mg daily with apixaban 5 mg BID increases bleeding risk, especially with current hematuria and indwelling catheter",
                "Co‑prescription of amitriptyline 100 mg nightly with sertraline 100 mg daily raises risk of serotonin syndrome and adds anticholinergic burden contributing to falls",
            ],
            intervention=[
                "Discontinue aspirin 75 mg daily",
                "Gradually reduce amitriptyline 100 mg nightly; continue sertraline for depression/anxiety and arrange a review of mood and sleep symptoms.",
                "Follow up: repeat urine dipstick in 1 week to ensure resolution of hematuria, monitor blood pressure after nitrate change, and reassess depressive symptoms in 4 weeks.",
            ],
            notes=[
                "Document that bleeding risk outweighs secondary CHD benefit while the patient is on therapeutic apixaban for recent pulmonary embolism."
                "Concurrent use of two nitrate preparations (sublingual GTN spray and nitroglycerin transdermal patch) in a patient with low blood pressure",
                "The GTN spray only lowers BP transiently and there is no need to be too concerned. It's not necessary to intervene as the impact on BP from SL nitrates is transient.",
            ],
        ),
    ),
    (
        dedent("""
        Issue 1
        Initial Issue: Potential methotrexate‑related hepatotoxicity
        Initial Evidence: Liver function tests on 29 Jan 2025 show gamma‑glutamyl transferase 341 IU/L (normal <50) and alkaline phosphatase 202 IU/L (normal <130) while the patient is on methotrexate 10 mg weekly (started 3 Dec 2024).
        Initial Intervention Required: True

        Clinician agrees with issue: True
        Clinician reasoning: 


        Issue 2
        Initial Issue: Duplicate bisoprolol prescriptions causing possible dosing error
        Initial Evidence: Two active repeat prescriptions: bisoprolol 2.5 mg taken at teatime and bisoprolol 1.25 mg taken each morning (both started 3 Dec 2024), resulting in a total daily dose of 3.75 mg from two separate scripts.
        Initial Intervention Required: True

        Clinician agrees with issue: False
        Clinician reasoning: I believe the intended total daily dose is 3.75mg which isn't possible to achieve with a single tablet


        Intervention
        Initial Intervention Required: True
        Initial Intervention: 1. Discontinue methotrexate immediately and arrange repeat liver function testing and hepatology review to assess the cause of the cholestatic picture. 2. Consolidate bisoprolol dosing: replace the two separate scripts (2.5 mg at tea‑time and 1.25 mg each morning) with a single prescription of an appropriate total dose (e.g., 3.75 mg once daily or a standard dose such as 5 mg daily) and cancel the redundant prescription.
        Clinician agrees with the intervention: no
        Clinician reasoning: The intervention is recommending a certain stop but in clinical practice, i think more information would be required before advising a definitive cessation of methotrexate. The risk of stopping abruptly is that it causes relapse of RA and pain, which is something to be avoided in anyone but perhaps even more so in someone at the end of life (she is on palliative care register). The LFT picture is one of cholestasis which isn't typically what we would expect if this derangement were caused by the drug. I would expect a more inflammatory picture and a derangement of the ALT if this were truly drug related. There are other causes of a cholestatic picture that need to be investigated. In clinical practice, it would be necessary to review the trend of the LFTs and any previous investigations of cholestatic causes.
        Intervention should be: Review trend in LFTs and correlate with timeline of methotrexate dosing
        review any previous investigations into cholestatic derangement (gall stones etc)
        Repeat LFTs and review ongoing need for methotrexate. I don't think that a prescriber would abruptly stop (but methotrexate is specialist only prescribing so this is not routine GP work) It would be referred back to the prescriber for discussion.
        I don't think bisoprolol dose suggestion is correct, it will lead to over or under dosing.
    """),
        GroundTruthAssessment(
            reasoning="The clinician agreed with the first issue, but disagreed with the second. They also didn't suggest any missed issues. The intervention here is particularly interesting because it's a case where the clinician disagreed with the intervention and provided a detailed rationale for why they disagreed. We must be careful to only take the specific actions recommended in their updated intervention (review trend in LFTs and correlate with timeline of methotrexate dosing, review any previous investigations into cholestatic derangement, and repeat LFTs and review ongoing need for methotrexate). The other actions do not constitute an intervention. The suggestion to consolidate bisoprolol dosing wasn't explicitly confirmed by the clinician, but given the length of their reasoning, it's likely they'd have disagreed with it explicitly if they thought it was incorrect. We won't add this as an intervention, but we will add it as a note. Note we only include the review parts, because the clinician explicitly stated that these were required.",
            issues=[
                "Potential methotrexate‑related hepatotoxicity",
            ],
            intervention=[
                "Review trend in liver function tests and correlate changes with the timeline of methotrexate dosing",
                "Review any previous investigations into cholestatic derangement",
                "Repeat liver function tests and review ongoing need for methotrexate",
            ],
            notes=[
                "The observed cholestatic LFT pattern (elevated GGT and ALP) is not typical of methotrexate‑induced hepatotoxicity, so alternative causes should be investigated before attributing it to the drug.",
                "The duplicate bisoprolol prescriptions likely reflect an intended total daily dose of 3.75 mg, which cannot be achieved with a single tablet; therefore no dosing error is assumed.",
            ],
        ),
    ),
]


def format_examples(examples: list[tuple[str, GroundTruthAssessment]]) -> str:
    result = ""

    for example in examples:
        text, ground_truth = example
        result += "\n<example>\n"
        result += "\n<initial-assessment>\n" + text + "\n</initial-assessment>\n"
        result += (
            "\n<ground-truth>\n" + ground_truth.model_dump_json(indent=2) + "\n</ground-truth>\n"
        )
        result += "\n</example>\n"
    return result
