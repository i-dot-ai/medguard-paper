-- Filter 043: Patients aged >75 years on loop diuretics who have not had a U&E in the previous 15 months
--
-- This filter identifies patients who:
-- 1. Are aged >75 years (strictly greater than 75)
-- 2. Have been prescribed a loop diuretic
-- 3. Have NOT had a computer-recorded check of their renal function and electrolytes in the previous 15 months (450 days)
--
-- Design decisions:
-- - Uses patient demographics for age calculation
-- - Uses GP Prescriptions table for medication prescriptions (consolidated prescription islands)
-- - Uses GP Events for renal function test recordings (U&E, serum creatinine, GFR measurements)
-- - Age >75 means strictly greater than (76+), not 75 or older
-- - Looks back 15 months (450 days) from prescription start for renal checks
-- - Prioritizes precision: only flags clear cases of prescription without monitoring
-- - Similar to PINCER filter 003 but loop diuretics only, and age >75 (not >=75)

WITH loop_diuretic_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- These codes match actual UK prescription data
    SELECT code FROM (VALUES
        -- Parent/international codes (substance level - for reference)
        ('372691009'),  -- Loop diuretic [PARENT]
        ('387475002'),  -- Furosemide
        ('387498005'),  -- Bumetanide
        ('108476002'),  -- Torasemide

        -- UK dm+d codes: Furosemide products (THESE MATCH PRESCRIPTIONS!)
        ('42294711000001100'),  -- Furosemide 20mg tablet
        ('42294911000001103'),  -- Furosemide 500mg tablet
        ('42294811000001108'),  -- Furosemide 40mg tablet
        ('8519911000001102'),   -- Furosemide 4mg/5ml oral solution
        ('12036211000001104'),  -- Furosemide 20mg/5ml oral solution
        ('12087711000001103'),  -- Furosemide 40mg/5ml oral solution
        ('12088111000001103'),  -- Furosemide 50mg/5ml oral solution

        -- UK dm+d codes: Bumetanide products
        ('42292511000001100'),  -- Bumetanide 1mg tablet
        ('42292711000001105'),  -- Bumetanide 5mg tablet
        ('30798811000001102'),  -- Bumetanide 5mg/5ml oral suspension

        -- UK dm+d codes: Torasemide products
        ('42299111000001100'),  -- Torasemide 5mg tablet
        ('42298911000001105'),  -- Torasemide 10mg tablet
        ('42337211000001103'),  -- Torasemide 20mg tablet
        ('42299011000001101')   -- Torasemide 2.5mg tablet
    ) AS t(code)
),

renal_function_test_codes AS (
    -- SNOMED codes for renal function tests
    -- Includes: U&E, serum creatinine, GFR measurements
    SELECT code FROM (VALUES
        ('252167001'),  -- Measurement of urea and electrolytes (procedure)
        ('113075003'),  -- Creatinine measurement, serum (procedure)
        ('70901006'),   -- Creatinine measurement (procedure)
        ('80274001'),   -- Glomerular filtration rate (observable entity)
        ('167179007'),  -- Renal function tests within reference range
        ('167180005'),  -- Renal function tests outside reference range
        ('182809008'),  -- Renal function monitoring
        ('313822004'),  -- Corrected serum creatinine measurement
        ('166316005'),  -- Urea and electrolytes within reference range
        ('166317001'),  -- Urea and electrolytes abnormal
        ('250621009'),  -- Finding of urea and electrolyte observations
        ('365757006'),  -- Finding of serum creatinine level
        ('166714005'),  -- Serum creatinine outside reference range
        ('166716007'),  -- Serum creatinine within reference range
        ('166717003'),  -- Serum creatinine above reference range
        ('166715006')   -- Serum creatinine below reference range
    ) AS t(code)
),

elderly_patients AS (
    -- Find patients aged >75 years (strictly greater than 75, i.e., 76+)
    -- Calculate age as of today from date of birth
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        p.Dob,
        DATE_DIFF('year', p.Dob, CURRENT_DATE) as age
    FROM {patient_view} p
    WHERE p.Dob IS NOT NULL
        AND DATE_DIFF('year', p.Dob, CURRENT_DATE) > 75
),

loop_diuretic_prescriptions AS (
    -- Find loop diuretic prescriptions in elderly patients
    SELECT DISTINCT
        ep.FK_Patient_Link_ID,
        p.medication_start_date,
        p.medication_end_date,
        p.medication_code,
        p.medication_name
    FROM elderly_patients ep
    INNER JOIN {gp_prescriptions} p
        ON ep.FK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE p.medication_code IN (SELECT code FROM loop_diuretic_codes)
),

renal_function_checks AS (
    -- Find all renal function test events
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        ge.EventDate as renal_check_date
    FROM {gp_events_enriched} ge
    WHERE ge.SuppliedCode IN (SELECT code FROM renal_function_test_codes)
),

prescriptions_without_recent_renal_check AS (
    -- Find prescriptions where there was NO renal check in the 15 months (450 days) before prescription start
    SELECT DISTINCT
        ldp.FK_Patient_Link_ID,
        ldp.medication_start_date,
        ldp.medication_end_date,
        ldp.medication_name
    FROM loop_diuretic_prescriptions ldp
    WHERE NOT EXISTS (
        -- Check if there's any renal function test in the 450 days before prescription start
        SELECT 1
        FROM renal_function_checks rfc
        WHERE rfc.FK_Patient_Link_ID = ldp.FK_Patient_Link_ID
            AND rfc.renal_check_date >= (ldp.medication_start_date - INTERVAL '450 days')
            AND rfc.renal_check_date <= ldp.medication_start_date
    )
)

-- Return patient IDs matching this filter with period dates
SELECT DISTINCT
    FK_Patient_Link_ID,
    43 as filter_id,
    medication_start_date as start_date,
    medication_end_date as end_date
FROM prescriptions_without_recent_renal_check;
