-- Filter 002: Prescription of aspirin at a dose >75mg daily for ≥1 month in a patient aged >65 years
--
-- This filter identifies patients who:
-- 1. Are aged >65 years
-- 2. Have been prescribed aspirin at a dose >75mg daily
-- 3. The aspirin prescription duration is ≥1 month (30 days)
--
-- Design decisions:
-- - Uses patient Dob to calculate age at time of prescription
-- - Uses GP Prescriptions table for medication prescriptions (consolidated prescription islands)
-- - Dose >75mg identified by medication code (e.g., 150mg, 300mg formulations)
-- - Duration calculated as difference between medication_start_date and medication_end_date
-- - 1 month defined as 30 days
-- - Low-dose aspirin (75mg daily) is appropriate for cardiovascular prophylaxis in elderly
-- - Higher doses increase bleeding risk without additional cardiovascular benefit in most cases
-- - Prioritizes precision: only flags clear cases where dose and duration criteria are met
-- - Risk level: 2 (moderate risk - increased bleeding risk)

WITH elderly_patients AS (
    -- Find patients aged >65 years
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        p.Dob,
        DATE_DIFF('year', p.Dob, CURRENT_DATE) as age
    FROM {patient_view} p
    WHERE p.Dob IS NOT NULL
        AND DATE_DIFF('year', p.Dob, CURRENT_DATE) > 65
),

high_dose_aspirin_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- These codes match actual UK prescription data
    -- Only includes aspirin formulations >75mg daily dose
    SELECT code FROM (VALUES
        -- Parent/international codes (substance level - for reference)
        ('387458008'),  -- Aspirin [PARENT]

        -- UK dm+d codes: Aspirin >75mg products (THESE MATCH PRESCRIPTIONS!)
        -- Excludes 75mg formulations (low-dose aspirin for prophylaxis)

        -- 150mg formulations
        ('42291411000001109'),  -- Aspirin 150mg suppository

        -- 300mg formulations
        ('42291711000001103'),  -- Aspirin 300mg tablet
        ('42291511000001108'),  -- Aspirin 300mg gastro-resistant tablet
        ('42291611000001107'),  -- Aspirin 300mg suppository
        ('39695211000001102'),  -- Aspirin 300mg tablet for oral suspension
        ('8280511000001107'),   -- Aspirin 300mg/5ml oral solution
        ('8280611000001106'),   -- Aspirin 300mg/5ml oral suspension

        -- Higher concentration oral solutions/suspensions (>75mg per dose)
        ('8280211000001109'),   -- Aspirin 225mg/5ml oral solution
        ('8280311000001101'),   -- Aspirin 225mg/5ml oral suspension
        ('12012111000001104'),  -- Aspirin 100mg/5ml oral solution
        ('11712811000001108')   -- Aspirin 100mg/5ml oral suspension

        -- Note: Excluded low-dose aspirin formulations (75mg and below):
        -- - 42292011000001108 (Aspirin 75mg tablet)
        -- - 42291911000001101 (Aspirin 75mg gastro-resistant tablet)
        -- - 42291811000001106 (Aspirin 75mg tablet for oral suspension)
        -- - 10064711000001104 (Aspirin 75mg effervescent tablets)
        -- - All oral solutions/suspensions ≤75mg/5ml
    ) AS t(code)
),

high_dose_aspirin_prescriptions AS (
    -- Find elderly patients prescribed high-dose aspirin for ≥30 days
    SELECT DISTINCT
        ep.FK_Patient_Link_ID,
        ep.age,
        p.medication_start_date,
        p.medication_end_date,
        p.medication_code,
        p.medication_name,
        DATE_DIFF('day', p.medication_start_date, p.medication_end_date) as duration_days
    FROM elderly_patients ep
    INNER JOIN {gp_prescriptions} p
        ON ep.FK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE p.medication_code IN (SELECT code FROM high_dose_aspirin_codes)
        AND DATE_DIFF('day', p.medication_start_date, p.medication_end_date) >= 30
        -- Ensure prescription occurred when patient was >65 years
        AND DATE_DIFF('year', ep.Dob, p.medication_start_date) > 65
)

-- Return patient IDs matching this filter with period dates
SELECT DISTINCT
    FK_Patient_Link_ID,
    '002' as filter_id,
    medication_start_date as start_date,
    medication_end_date as end_date
FROM high_dose_aspirin_prescriptions;
