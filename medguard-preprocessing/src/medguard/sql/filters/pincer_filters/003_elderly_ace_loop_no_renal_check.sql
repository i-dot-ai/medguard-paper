-- Filter 003: Patients aged 75 years and older who have been prescribed an ACE inhibitor or loop diuretic long-term without recent renal function check
--
-- This filter identifies patients who:
-- 1. Are aged 75 years or older
-- 2. Have been prescribed an ACE inhibitor or loop diuretic long-term (prescription duration >= 90 days)
-- 3. Have NOT had a computer-recorded check of their renal function and electrolytes in the previous 15 months (450 days)
--
-- Design decisions:
-- - Uses patient demographics for age calculation
-- - Uses GP Prescriptions table for medication prescriptions (consolidated prescription islands)
-- - Uses GP Events for renal function test recordings
-- - "Long-term" defined as prescription duration >= 90 days
-- - Renal function checks include: U&E, serum creatinine, GFR measurements
-- - Looks back 15 months (450 days) from prescription start for renal checks
-- - Prioritizes precision: only flags clear cases of long-term prescription without monitoring

WITH ace_inhibitor_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- These codes match actual UK prescription data
    SELECT code FROM (VALUES
        -- Parent/international codes (substance level - for reference)
        ('372733002'),  -- ACE inhibitor [PARENT]
        ('386872004'),  -- Ramipril
        ('372658000'),  -- Enalapril
        ('386873009'),  -- Lisinopril
        ('372916001'),  -- Perindopril

        -- UK dm+d codes: Ramipril products (THESE MATCH PRESCRIPTIONS!)
        ('42381311000001109'),  -- Ramipril 10mg tablet
        ('42381711000001108'),  -- Ramipril 5mg tablet
        ('42381511000001103'),  -- Ramipril 2.5mg tablet
        ('42381111000001107'),  -- Ramipril 1.25mg tablet
        ('42381211000001101'),  -- Ramipril 10mg capsule
        ('42381611000001104'),  -- Ramipril 5mg capsule
        ('42381411000001102'),  -- Ramipril 2.5mg capsule
        ('42381011000001106'),  -- Ramipril 1.25mg capsule
        ('5624411000001103'),   -- Ramipril 5mg capsules (Sandoz)
        ('5624611000001100'),   -- Ramipril 10mg capsules (Sandoz)
        ('11533811000001108'),  -- Ramipril 5mg tablets (Sandoz)
        ('11534011000001100'),  -- Ramipril 10mg tablets (Sandoz)

        -- UK dm+d codes: Lisinopril products
        ('42376411000001104'),  -- Lisinopril 20mg tablet
        ('42376111000001109'),  -- Lisinopril 10mg tablet
        ('42376511000001100'),  -- Lisinopril 5mg tablet
        ('42376211000001103'),  -- Lisinopril 2.5mg tablet
        ('683211000001108'),    -- Lisinopril 5mg tablets (Sandoz)
        ('145811000001100'),    -- Lisinopril 10mg tablets (Sandoz)
        ('637111000001101'),    -- Lisinopril 20mg tablets (Sandoz)
        ('877611000001104'),    -- Lisinopril 2.5mg tablets (Sandoz)

        -- UK dm+d codes: Enalapril products
        ('42374311000001100'),  -- Enalapril 5mg tablet
        ('42374211000001108'),  -- Enalapril 20mg tablet
        ('42374011000001103'),  -- Enalapril 10mg tablet
        ('42374111000001102'),  -- Enalapril 2.5mg tablet
        ('728411000001104'),    -- Enalapril 20mg tablets (Sandoz)
        ('450811000001105'),    -- Enalapril 10mg tablets (Sandoz)
        ('51511000001108'),     -- Enalapril 5mg tablets (Sandoz)
        ('395411000001101'),    -- Enalapril 2.5mg tablets (Sandoz)

        -- UK dm+d codes: Perindopril products
        ('42379211000001107'),  -- Perindopril erbumine 2mg tablet
        ('42379311000001104'),  -- Perindopril erbumine 4mg tablet
        ('42379411000001106'),  -- Perindopril erbumine 8mg tablet
        ('13651711000001102'),  -- Perindopril erbumine 2mg tablets (Sandoz)
        ('13652011000001107'),  -- Perindopril erbumine 4mg tablets (Sandoz)
        ('20319211000001109'),  -- Perindopril erbumine 8mg tablets (Sandoz)
        ('13454111000001103'),  -- Perindopril arginine 10mg tablets
        ('13454411000001108'),  -- Perindopril arginine 5mg tablets
        ('13454211000001109')   -- Perindopril arginine 2.5mg tablets
    ) AS t(code)
),

loop_diuretic_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- These codes match actual UK prescription data
    SELECT code FROM (VALUES
        -- Parent/international codes (substance level - for reference)
        ('372691009'),  -- Loop diuretic [PARENT]
        ('387475002'),  -- Furosemide
        ('387498005'),  -- Bumetanide

        -- UK dm+d codes: Furosemide products (THESE MATCH PRESCRIPTIONS!)
        ('42294711000001100'),  -- Furosemide 20mg tablet
        ('42294911000001103'),  -- Furosemide 500mg tablet
        ('42294811000001108'),  -- Furosemide 40mg tablet
        ('662811000001104'),    -- Furosemide 20mg tablets (Sandoz)
        ('864611000001104'),    -- Furosemide 40mg tablets (Sandoz)
        ('8519911000001102'),   -- Furosemide 4mg/5ml oral solution
        ('12036211000001104'),  -- Furosemide 20mg/5ml oral solution
        ('12087711000001103'),  -- Furosemide 40mg/5ml oral solution

        -- UK dm+d codes: Bumetanide products
        ('42292511000001100'),  -- Bumetanide 1mg tablet
        ('42292711000001105'),  -- Bumetanide 5mg tablet
        ('30798811000001102')   -- Bumetanide 5mg/5ml oral suspension
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
    -- Find patients aged 75 or older
    -- Calculate age as of today from date of birth
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        p.Dob,
        DATE_DIFF('year', p.Dob, CURRENT_DATE) as age
    FROM {patient_view} p
    WHERE p.Dob IS NOT NULL
        AND DATE_DIFF('year', p.Dob, CURRENT_DATE) >= 75
),

long_term_prescriptions AS (
    -- Find long-term ACE inhibitor or loop diuretic prescriptions (>= 90 days)
    SELECT DISTINCT
        ep.FK_Patient_Link_ID,
        p.medication_start_date,
        p.medication_end_date,
        p.medication_code,
        p.medication_name,
        DATE_DIFF('day', p.medication_start_date, p.medication_end_date) as prescription_duration_days
    FROM elderly_patients ep
    INNER JOIN {gp_prescriptions} p
        ON ep.FK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE (p.medication_code IN (SELECT code FROM ace_inhibitor_codes)
           OR p.medication_code IN (SELECT code FROM loop_diuretic_codes))
        AND DATE_DIFF('day', p.medication_start_date, p.medication_end_date) >= 90
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
        ltp.FK_Patient_Link_ID,
        ltp.medication_start_date,
        ltp.medication_end_date,
        ltp.medication_name
    FROM long_term_prescriptions ltp
    WHERE NOT EXISTS (
        -- Check if there's any renal function test in the 450 days before prescription start
        SELECT 1
        FROM renal_function_checks rfc
        WHERE rfc.FK_Patient_Link_ID = ltp.FK_Patient_Link_ID
            AND rfc.renal_check_date >= (ltp.medication_start_date - INTERVAL '450 days')
            AND rfc.renal_check_date <= ltp.medication_start_date
    )
)

-- Return patient IDs matching this filter with period dates
SELECT DISTINCT
    FK_Patient_Link_ID,
    '003' as filter_id,
    medication_start_date as start_date,
    medication_end_date as end_date
FROM prescriptions_without_recent_renal_check;
