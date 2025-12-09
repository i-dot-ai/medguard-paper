-- Filter 009: Initiation of prescription of benzodiazepine or Z drugs for ≥21 days in a patient aged >65 years with depression
--
-- This filter identifies patients who:
-- 1. Are aged >65 years at time of prescription
-- 2. Have a recorded diagnosis of depression (any type)
-- 3. Have been prescribed a benzodiazepine or Z-drug for ≥21 days AFTER depression diagnosis
-- 4. This is an INITIATION (no prior benzodiazepine/Z-drug use in last 450 days)
--
-- Design decisions:
-- - Uses patient Dob to calculate age at time of prescription
-- - Uses GP Events for depression diagnoses
-- - Uses GP Prescriptions table for medication prescriptions (consolidated prescription islands)
-- - Duration ≥21 days calculated from medication_start_date to medication_end_date
-- - "Initiation" defined as: no benzodiazepine/Z-drug prescriptions in the 450 days (15 months) before current prescription start
-- - Prescription must occur AFTER depression diagnosis
-- - Benzodiazepines: diazepam, lorazepam, temazepam, clonazepam, nitrazepam, alprazolam
-- - Z-drugs: zopiclone, zolpidem
-- - Clinical rationale: Benzodiazepines/Z-drugs can worsen depression, increase suicide risk, cause dependence
-- - Non-pharmacological approaches preferred for depression-related insomnia/anxiety in elderly
-- - Risk level: 3 (significant risk - worsening depression, suicide risk, falls, dependence)

WITH depression_codes AS (
    -- SNOMED codes for depression and all descendants
    -- Based on concept_id 35489007 (Depressive disorder)
    SELECT code FROM (VALUES
        ('35489007'),   -- Depressive disorder [PARENT]
        ('191659001'),  -- Atypical depressive disorder
        ('231485007'),  -- Post-schizophrenic depression
        ('231500002'),  -- Masked depression
        ('300706003'),  -- Endogenous depression
        ('48589009'),   -- Minor depressive disorder
        ('58703003'),   -- Postpartum depression
        ('78667006'),   -- Dysthymia
        ('79842004'),   -- Stuporous depression
        ('82218004'),   -- Postoperative depression
        ('83458005'),   -- Agitated depression
        ('84760002'),   -- Schizoaffective disorder, depressive type
        ('84788008'),   -- Menopausal depression
        ('191616006'),  -- Recurrent depression
        ('192080009'),  -- Chronic depression
        ('310495003'),  -- Mild depression
        ('310496002'),  -- Moderate depression
        ('310497006'),  -- Severe depression
        ('191627008'),  -- Bipolar affective disorder, current episode depression
        ('370143000'),  -- Major depressive disorder
        ('87414006'),   -- Reactive depression (situational)
        ('442057004'),  -- Chronic depressive personality disorder
        ('712823008'),  -- Acute depression
        ('231504006'),  -- Mixed anxiety and depressive disorder
        ('788120007'),  -- Antenatal depression
        ('1153570009'), -- Treatment resistant depression
        ('1153575004'), -- Persistent depressive disorder
        ('413296003'),  -- Depression requiring intervention
        ('321717001'),  -- Involutional depression
        ('231499006'),  -- Endogenous depression first episode
        ('274948002'),  -- Endogenous depression - recurrent
        ('596004'),     -- Premenstrual dysphoric disorder
        ('237349002'),  -- Mild postnatal depression
        ('237350002'),  -- Severe postnatal depression
        ('279225001'),  -- Maternity blues
        ('25922000'),   -- Major depressive disorder, single episode with postpartum onset
        ('71336009'),   -- Recurrent major depressive disorder with postpartum onset
        ('19694002'),   -- Late onset dysthymia
        ('2506003'),    -- Early onset dysthymia
        ('83176005'),   -- Primary dysthymia
        ('85080004'),   -- Secondary dysthymia
        ('40568001'),   -- Recurrent brief depressive disorder
        ('66344007'),   -- Recurrent major depression
        ('247803002'),  -- Seasonal affective disorder
        ('2618002'),    -- Chronic recurrent major depressive disorder
        ('87512008'),   -- Mild major depression
        ('832007'),     -- Moderate major depression
        ('450714000'),  -- Severe major depression
        ('36923009'),   -- Major depression, single episode
        ('42810003'),   -- Major depressive disorder in remission
        ('720455008'),  -- Minimal major depression
        ('726772006'),  -- Major depression with psychotic features
        ('719592004'),  -- Moderately severe major depression
        ('191495003')   -- Depressive disorder caused by drug
    ) AS t(code)
),

benzodiazepine_zdrug_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- These codes match actual UK prescription data
    -- Includes benzodiazepines and Z-drugs (non-benzodiazepine hypnotics)
    SELECT code FROM (VALUES
        -- Parent/international codes (substance level - for reference)
        ('387173000'),  -- Diazepam [PARENT]
        ('387106007'),  -- Lorazepam [PARENT]
        ('387481004'),  -- Temazepam [PARENT]
        ('387569009'),  -- Clonazepam [PARENT]
        ('387399006'),  -- Nitrazepam [PARENT]
        ('386983007'),  -- Alprazolam [PARENT]
        ('386847004'),  -- Zopiclone [PARENT]
        ('386849001'),  -- Zolpidem [PARENT]

        -- UK dm+d codes: Diazepam products (benzodiazepine)
        ('1257511000001107'),  -- Diazepam 2mg tablets 28 tablet
        ('998211000001100'),   -- Diazepam 2mg tablets 1000 tablet
        ('1059411000001108'),  -- Diazepam 5mg tablets 1000 tablet
        ('1116611000001102'),  -- Diazepam 5mg tablets 28 tablet
        ('1289511000001106'),  -- Diazepam 10mg tablets 500 tablet
        ('1132211000001105'),  -- Diazepam 10mg tablets 28 tablet
        ('9107111000001103'),  -- Diazepam 2mg tablets 500 tablet
        ('9107011000001104'),  -- Diazepam 2mg tablets 100 tablet
        ('9106611000001109'),  -- Diazepam 10mg tablets 100 tablet
        ('8792711000001108'),  -- Diazepam 10mg/5ml oral solution
        ('8792811000001100'),  -- Diazepam 1mg/5ml oral solution
        ('13893211000001109'), -- Diazepam 10mg/5ml oral suspension
        ('19677811000001102'), -- Diazepam 2mg/5ml oral suspension
        ('3823911000001106'),  -- Diazepam 10mg suppositories 6 suppository

        -- UK dm+d codes: Lorazepam products (benzodiazepine)
        ('1114711000001102'),  -- Lorazepam 1mg tablets 28 tablet
        ('10545111000001106'), -- Lorazepam 1mg tablets 30 tablet
        ('15171111000001109'), -- Lorazepam 1mg tablets 100 tablet
        ('15171011000001108'), -- Lorazepam 1mg tablets 50 tablet
        ('15473311000001108'), -- Lorazepam 1mg tablets 1000 tablet
        ('8659111000001104'),  -- Lorazepam 250micrograms/5ml oral solution
        ('8659411000001109'),  -- Lorazepam 2mg/5ml oral solution
        ('8659211000001105'),  -- Lorazepam 250micrograms/5ml oral suspension
        ('8659511000001108'),  -- Lorazepam 2mg/5ml oral suspension
        ('8659611000001107'),  -- Lorazepam 500micrograms/5ml oral solution
        ('8659911000001101'),  -- Lorazepam 5mg/5ml oral solution
        ('8659811000001106'),  -- Lorazepam 500micrograms/5ml oral suspension
        ('8660011000001104'),  -- Lorazepam 5mg/5ml oral suspension

        -- UK dm+d codes: Temazepam products (benzodiazepine)
        ('1130911000001100'),  -- Temazepam 20mg tablets 7 tablet
        ('1118111000001109'),  -- Temazepam 20mg tablets 250 tablet
        ('1227811000001109'),  -- Temazepam 20mg tablets 28 tablet
        ('989211000001109'),   -- Temazepam 10mg tablets 500 tablet
        ('1259211000001103'),  -- Temazepam 10mg tablets 28 tablet
        ('1178811000001105'),  -- Temazepam 10mg tablets 7 tablet
        ('13302211000001103'), -- Temazepam 14mg/5ml oral solution
        ('13302311000001106'), -- Temazepam 14mg/5ml oral suspension

        -- UK dm+d codes: Clonazepam products (benzodiazepine)
        ('958011000001104'),   -- Clonazepam 2mg tablets 100 tablet
        ('1063711000001105'),  -- Clonazepam 500microgram tablets 100 tablet
        ('8382911000001108'),  -- Clonazepam 10mg/5ml oral solution
        ('8383011000001100'),  -- Clonazepam 10mg/5ml oral suspension
        ('8395511000001108'),  -- Clonazepam 200micrograms/5ml oral solution
        ('8395611000001107'),  -- Clonazepam 200micrograms/5ml oral suspension
        ('8395111000001104'),  -- Clonazepam 1mg/5ml oral solution
        ('8395911000001101'),  -- Clonazepam 2mg/5ml oral solution
        ('8395211000001105'),  -- Clonazepam 1mg/5ml oral suspension
        ('8396011000001109'),  -- Clonazepam 2mg/5ml oral suspension
        ('17870411000001103'), -- Clonazepam 500microgram orodispersible tablets

        -- UK dm+d codes: Nitrazepam products (benzodiazepine)
        ('1314411000001101'),  -- Nitrazepam 5mg tablets 30 tablet
        ('1021511000001107'),  -- Nitrazepam 5mg tablets 500 tablet
        ('1004511000001101'),  -- Nitrazepam 5mg tablets 28 tablet
        ('12141311000001107'), -- Nitrazepam 2mg/5ml oral suspension
        ('12141511000001101'), -- Nitrazepam 4mg/5ml oral suspension
        ('12141611000001102'), -- Nitrazepam 6mg/5ml oral suspension
        ('12144111000001108'), -- Nitrazepam 10mg/5ml oral suspension
        ('8642011000001105'),  -- Nitrazepam 5mg/5ml oral suspension 1 ml

        -- UK dm+d codes: Alprazolam products (benzodiazepine)
        ('4659211000001109'),  -- Alprazolam 500microgram tablets 60 tablet
        ('4658311000001107'),  -- Alprazolam 250microgram tablets 60 tablet

        -- UK dm+d codes: Zopiclone products (Z-drug)
        ('1166611000001103'),  -- Zopiclone 7.5mg tablets 28 tablet
        ('1313311000001106'),  -- Zopiclone 3.75mg tablets 28 tablet
        ('10464011000001105'), -- Zopiclone 7.5mg tablets 30 tablet
        ('13018211000001103'), -- Zopiclone 5mg/5ml oral suspension
        ('8799011000001104'),  -- Zopiclone 3.75mg/5ml oral suspension
        ('19609611000001101'), -- Zopiclone 3.75mg/5ml oral solution
        ('8798911000001108'),  -- Zopiclone 7.5mg/5ml oral suspension
        ('24510911000001105'), -- Zopiclone 7.5mg/5ml oral solution

        -- UK dm+d codes: Zolpidem products (Z-drug)
        ('3205711000001109'),  -- Zolpidem 5mg tablets 28 tablet
        ('3199211000001104'),  -- Zolpidem 10mg tablets 28 tablet
        ('5414211000001109'),  -- Zolpidem 10mg tablets 30 tablet
        ('15857711000001109'), -- Zolpidem 5mg oral powder sachets
        ('15854411000001108')  -- Zolpidem 5mg oral powder sachets 1 sachet
    ) AS t(code)
),

elderly_patients AS (
    -- Find patients aged >65 years
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        p.Dob
    FROM {patient_view} p
    WHERE p.Dob IS NOT NULL
),

patients_with_depression AS (
    -- Find patients with depression diagnosis from GP events
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        MIN(ge.EventDate) as earliest_depression_date
    FROM {gp_events_enriched} ge
    WHERE ge.SuppliedCode IN (SELECT code FROM depression_codes)
    GROUP BY ge.FK_Patient_Link_ID
),

elderly_depression_prescriptions AS (
    -- Find benzodiazepine/Z-drug prescriptions in elderly patients with depression
    -- Prescription must be AFTER depression diagnosis, duration ≥21 days, patient >65 years old
    SELECT DISTINCT
        ep.FK_Patient_Link_ID,
        ep.Dob,
        pd.earliest_depression_date,
        p.medication_start_date,
        p.medication_end_date,
        p.medication_code,
        p.medication_name,
        DATE_DIFF('day', p.medication_start_date, p.medication_end_date) as duration_days,
        DATE_DIFF('year', ep.Dob, p.medication_start_date) as age_at_prescription
    FROM elderly_patients ep
    INNER JOIN patients_with_depression pd
        ON ep.FK_Patient_Link_ID = pd.FK_Patient_Link_ID
    INNER JOIN {gp_prescriptions} p
        ON ep.FK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE p.medication_code IN (SELECT code FROM benzodiazepine_zdrug_codes)
        -- Prescription occurred when patient was >65 years
        AND DATE_DIFF('year', ep.Dob, p.medication_start_date) > 65
        -- Duration ≥21 days
        AND DATE_DIFF('day', p.medication_start_date, p.medication_end_date) >= 21
        -- Prescription started AFTER depression diagnosis
        AND p.medication_start_date >= pd.earliest_depression_date
),

prior_use_check AS (
    -- For each prescription, check if patient had ANY benzodiazepine/Z-drug prescription
    -- in the 450 days (15 months) BEFORE the current prescription started
    -- This identifies INITIATION (no prior use)
    SELECT DISTINCT
        edp.FK_Patient_Link_ID,
        edp.medication_start_date,
        edp.medication_end_date,
        edp.medication_code,
        edp.medication_name,
        COUNT(DISTINCT prior.medication_start_date) as prior_prescription_count
    FROM elderly_depression_prescriptions edp
    LEFT JOIN {gp_prescriptions} prior
        ON edp.FK_Patient_Link_ID = prior.FK_Patient_Link_ID
        AND prior.medication_code IN (SELECT code FROM benzodiazepine_zdrug_codes)
        -- Prior prescription must have ended before current prescription started
        -- AND within 450 days before current prescription start (lookback window)
        AND prior.medication_end_date < edp.medication_start_date
        AND prior.medication_end_date >= (edp.medication_start_date - INTERVAL '450 days')
    GROUP BY
        edp.FK_Patient_Link_ID,
        edp.medication_start_date,
        edp.medication_end_date,
        edp.medication_code,
        edp.medication_name
),

new_inappropriate_prescriptions AS (
    -- Only include prescriptions where patient has NO prior benzodiazepine/Z-drug use
    -- These are NEW prescriptions (INITIATION) in elderly patients with depression
    SELECT
        FK_Patient_Link_ID,
        medication_start_date,
        medication_end_date,
        medication_code,
        medication_name
    FROM prior_use_check
    WHERE prior_prescription_count = 0  -- No prior use in last 450 days (INITIATION)
)

-- Return patient IDs matching this filter with period dates
SELECT DISTINCT
    FK_Patient_Link_ID,
    '009' as filter_id,
    medication_start_date as start_date,
    medication_end_date as end_date
FROM new_inappropriate_prescriptions;
