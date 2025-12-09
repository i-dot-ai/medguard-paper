-- Filter 045: Amiodarone prescription without thyroid function test in previous 9 months
--
-- This filter identifies patients who:
-- 1. Have been prescribed amiodarone
-- 2. Have NOT had a thyroid function test recorded in the previous 9 months (270 days) before prescription start
--
-- Design decisions:
-- - Uses GP Prescriptions table for amiodarone prescriptions (consolidated prescription islands)
-- - Uses GP Events for thyroid function test recordings
-- - Thyroid function tests include: thyroid panel, TSH measurement, T4/thyroxine measurement
-- - Looks back 9 months (270 days) from prescription start for thyroid checks
-- - Prioritizes precision: only flags clear cases of prescription without monitoring
--
-- Clinical context:
-- - Amiodarone can cause both hypothyroidism and hyperthyroidism (hypo more common)
-- - Contains high iodine content that affects thyroid function
-- - BNF recommends thyroid function tests before treatment and every 6 months
-- - This filter uses 9-month window to allow for some flexibility in monitoring intervals

WITH amiodarone_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    SELECT code FROM (VALUES
        -- Parent/international codes (substance level - for reference)
        ('372821002'),  -- Amiodarone (substance)

        -- UK dm+d codes: Amiodarone products (THESE MATCH PRESCRIPTIONS!)
        ('42291011000001100'),  -- Amiodarone 200mg tablet
        ('42290911000001108'),  -- Amiodarone 100mg tablet

        -- Oral solutions/suspensions
        ('8275311000001103'),   -- Amiodarone 25mg/5ml oral solution
        ('8276111000001106'),   -- Amiodarone 50mg/5ml oral solution
        ('8276811000001104'),   -- Amiodarone 75mg/5ml oral solution
        ('8275011000001101'),   -- Amiodarone 250mg/5ml oral solution
        ('8275511000001109'),   -- Amiodarone 30mg/5ml oral solution
        ('8276311000001108'),   -- Amiodarone 60mg/5ml oral solution
        ('8277011000001108'),   -- Amiodarone 85mg/5ml oral solution
        ('8274311000001102'),   -- Amiodarone 100mg/5ml oral solution
        ('8274511000001108'),   -- Amiodarone 200mg/5ml oral solution
        ('8274711000001103'),   -- Amiodarone 20mg/5ml oral solution
        ('11708811000001108'),  -- Amiodarone 10mg/5ml oral solution
        ('11709011000001107'),  -- Amiodarone 125mg/5ml oral solution
        ('11709211000001102'),  -- Amiodarone 150mg/5ml oral solution
        ('11709411000001103'),  -- Amiodarone 155mg/5ml oral solution
        ('11709611000001100'),  -- Amiodarone 15mg/5ml oral solution
        ('11709811000001101'),  -- Amiodarone 22mg/5ml oral solution
        ('11710011000001101'),  -- Amiodarone 35mg/5ml oral solution
        ('11710211000001106'),  -- Amiodarone 45mg/5ml oral solution
        ('11710411000001105'),  -- Amiodarone 500mg/5ml oral solution
        ('11710611000001108'),  -- Amiodarone 5mg/5ml oral solution

        -- Oral powder
        ('8816011000001108')    -- Amiodarone 55mg oral powder sachets
    ) AS t(code)
),

thyroid_function_test_codes AS (
    -- SNOMED codes for thyroid function tests
    -- Includes: thyroid panel, TSH, T4/thyroxine measurements
    SELECT code FROM (VALUES
        -- General thyroid function tests
        ('35650009'),   -- Thyroid panel (procedure)
        ('1016851000000107'),  -- Thyroid function test
        ('312397004'),  -- Thyroid function tests normal (finding)
        ('312399001'),  -- Thyroid function tests abnormal (finding)

        -- TSH (Thyroid Stimulating Hormone) measurements
        ('61167004'),   -- Thyroid stimulating hormone measurement (procedure)
        ('313440008'),  -- Measurement of serum thyroid stimulating hormone
        ('313441007'),  -- Measurement of plasma thyroid stimulating hormone
        ('401102003'),  -- Blood spot thyroid stimulating hormone level

        -- T4/Thyroxine measurements
        ('72765002'),   -- Thyroxine measurement (procedure)
        ('313408009'),  -- Total thyroxine measurement (procedure)
        ('5113004'),    -- T4 free measurement (procedure)
        ('1030801000000101'),  -- Free thyroxine level
        ('131092009'),  -- Thyroxine level above reference range
        ('131093004'),  -- Thyroxine level below reference range
        ('166330000'),  -- Serum thyroxine level within reference range
        ('166331001'),  -- Serum thyroxine level outside reference range

        -- T3 measurements (sometimes included in thyroid panel)
        ('252374002'),  -- Triiodothyronine measurement
        ('61167007')    -- Free triiodothyronine measurement
    ) AS t(code)
),

amiodarone_prescriptions AS (
    -- Find all amiodarone prescriptions
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        p.medication_start_date,
        p.medication_end_date,
        p.medication_code,
        p.medication_name
    FROM {gp_prescriptions} p
    WHERE p.medication_code IN (SELECT code FROM amiodarone_codes)
),

thyroid_function_checks AS (
    -- Find all thyroid function test events
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        ge.EventDate as thyroid_check_date
    FROM {gp_events_enriched} ge
    WHERE ge.SuppliedCode IN (SELECT code FROM thyroid_function_test_codes)
),

prescriptions_without_recent_thyroid_check AS (
    -- Find prescriptions where there was NO thyroid check in the 9 months (270 days) before prescription start
    SELECT DISTINCT
        ap.FK_Patient_Link_ID,
        ap.medication_start_date,
        ap.medication_end_date,
        ap.medication_name
    FROM amiodarone_prescriptions ap
    WHERE NOT EXISTS (
        -- Check if there's any thyroid function test in the 270 days before prescription start
        SELECT 1
        FROM thyroid_function_checks tfc
        WHERE tfc.FK_Patient_Link_ID = ap.FK_Patient_Link_ID
            AND tfc.thyroid_check_date >= (ap.medication_start_date - INTERVAL '270 days')
            AND tfc.thyroid_check_date <= ap.medication_start_date
    )
)

-- Return patient IDs matching this filter with period dates
SELECT DISTINCT
    FK_Patient_Link_ID,
    '045' as filter_id,
    medication_start_date as start_date,
    medication_end_date as end_date
FROM prescriptions_without_recent_thyroid_check;
