-- Filter 008: Prescription of a benzodiazepine or Z drug for ≥21 days, in a patient aged >65 years, who is not receiving benzodiazepines or Z drugs on a long-term basis
--
-- This filter identifies patients who:
-- 1. Are aged >65 years at time of prescription
-- 2. Have been prescribed a benzodiazepine or Z-drug for ≥21 days
-- 3. Do NOT have a history of long-term benzodiazepine/Z-drug use (no prescriptions in prior 450 days)
--
-- Design decisions:
-- - Uses patient Dob to calculate age at time of prescription
-- - Uses GP Prescriptions table for medication prescriptions (consolidated prescription islands)
-- - Duration ≥21 days calculated from medication_start_date to medication_end_date
-- - "Not receiving on a long-term basis" defined as: no benzodiazepine/Z-drug prescriptions in the 450 days (15 months) before current prescription start
-- - This identifies NEW inappropriate long prescriptions in elderly patients (not those already on chronic therapy)
-- - Benzodiazepines: diazepam, lorazepam, temazepam, clonazepam, nitrazepam, alprazolam, etc.
-- - Z-drugs: zopiclone, zolpidem, zaleplon
-- - Clinical rationale: Benzodiazepines/Z-drugs increase fall risk, cognitive impairment, dependence in elderly
-- - Chronic users may have legitimate need; this targets NEW inappropriate prescriptions
-- - Risk level: 3 (significant risk - falls, cognitive impairment, dependence)

WITH elderly_patients AS (
    -- Find patients aged >65 years
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        p.Dob
    FROM {patient_view} p
    WHERE p.Dob IS NOT NULL
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

        -- Note: This list includes the most common benzodiazepine and Z-drug formulations
        -- Additional brand names and pack sizes exist but core products are covered
    ) AS t(code)
),

elderly_prescriptions AS (
    -- Find benzodiazepine/Z-drug prescriptions in elderly patients (>65 years) with duration ≥21 days
    SELECT DISTINCT
        ep.FK_Patient_Link_ID,
        ep.Dob,
        p.medication_start_date,
        p.medication_end_date,
        p.medication_code,
        p.medication_name,
        DATE_DIFF('day', p.medication_start_date, p.medication_end_date) as duration_days,
        DATE_DIFF('year', ep.Dob, p.medication_start_date) as age_at_prescription
    FROM elderly_patients ep
    INNER JOIN {gp_prescriptions} p
        ON ep.FK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE p.medication_code IN (SELECT code FROM benzodiazepine_zdrug_codes)
        -- Prescription occurred when patient was >65 years
        AND DATE_DIFF('year', ep.Dob, p.medication_start_date) > 65
        -- Duration ≥21 days
        AND DATE_DIFF('day', p.medication_start_date, p.medication_end_date) >= 21
),

prior_use_check AS (
    -- For each prescription, check if patient had ANY benzodiazepine/Z-drug prescription
    -- in the 450 days (15 months) BEFORE the current prescription started
    -- This identifies patients with prior long-term use (who should be excluded)
    SELECT DISTINCT
        ep.FK_Patient_Link_ID,
        ep.medication_start_date,
        ep.medication_end_date,
        ep.medication_code,
        ep.medication_name,
        COUNT(DISTINCT prior.medication_start_date) as prior_prescription_count
    FROM elderly_prescriptions ep
    LEFT JOIN {gp_prescriptions} prior
        ON ep.FK_Patient_Link_ID = prior.FK_Patient_Link_ID
        AND prior.medication_code IN (SELECT code FROM benzodiazepine_zdrug_codes)
        -- Prior prescription must have ended before current prescription started
        -- AND within 450 days before current prescription start (lookback window)
        AND prior.medication_end_date < ep.medication_start_date
        AND prior.medication_end_date >= (ep.medication_start_date - INTERVAL '450 days')
    GROUP BY
        ep.FK_Patient_Link_ID,
        ep.medication_start_date,
        ep.medication_end_date,
        ep.medication_code,
        ep.medication_name
),

new_inappropriate_prescriptions AS (
    -- Only include prescriptions where patient has NO prior benzodiazepine/Z-drug use
    -- These are NEW prescriptions in elderly patients (not chronic therapy)
    SELECT
        FK_Patient_Link_ID,
        medication_start_date,
        medication_end_date,
        medication_code,
        medication_name
    FROM prior_use_check
    WHERE prior_prescription_count = 0  -- No prior use in last 450 days
)

-- Return patient IDs matching this filter with period dates
SELECT DISTINCT
    FK_Patient_Link_ID,
    '008' as filter_id,
    medication_start_date as start_date,
    medication_end_date as end_date
FROM new_inappropriate_prescriptions;
