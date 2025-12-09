-- Filter 003: Prescription of digoxin at a dose >125 micrograms daily in a patient with renal impairment (for example, CKD 3 or worse)
--
-- This filter identifies patients who:
-- 1. Have a recorded diagnosis of renal impairment or chronic kidney disease (CKD) stage 3 or worse
-- 2. Have been prescribed digoxin at a dose >125 micrograms daily (i.e., 250 micrograms)
--
-- Design decisions:
-- - Uses GP Events for CKD/renal impairment diagnoses
-- - Uses GP Prescriptions table for medication prescriptions
-- - Renal impairment includes: CKD stage 3, 3A, 3B, 4, 5, and general renal impairment diagnoses
-- - Dose >125 micrograms means 250 microgram formulations (standard digoxin strengths: 62.5, 125, 250 mcg)
-- - Note: CSV states ">125 mg" but this is a typo - digoxin is dosed in micrograms (mcg), not milligrams
-- - In renal impairment, digoxin clearance is reduced, requiring dose reduction to avoid toxicity
-- - Standard dose in renal impairment should be 62.5-125 micrograms; 250 micrograms is too high
-- - Prioritizes precision: only flags clear cases where high-dose digoxin is prescribed after CKD diagnosis
-- - Risk level: 3 (significant risk of digoxin toxicity)

WITH renal_impairment_codes AS (
    -- SNOMED codes for chronic kidney disease stage 3+ and renal impairment
    SELECT code FROM (VALUES
        -- General renal impairment
        ('236423003'),  -- Renal impairment (disorder)
        ('709044004'),  -- Chronic kidney disease (disorder)

        -- CKD stage 3 and worse (eGFR <60)
        ('433144002'),  -- Chronic kidney disease stage 3
        ('700378005'),  -- Chronic kidney disease stage 3A (eGFR 45-59)
        ('700379002'),  -- Chronic kidney disease stage 3B (eGFR 30-44)
        ('431857002'),  -- Chronic kidney disease stage 4 (eGFR 15-29)
        ('433146000'),  -- Chronic kidney disease stage 5 (eGFR <15)
        ('714152005'),  -- Chronic kidney disease stage 5 on dialysis
        ('714153000'),  -- Chronic kidney disease stage 5 with transplant

        -- CKD stage 3 subtypes with proteinuria status
        ('324251000000105'),  -- Chronic kidney disease stage 3 with proteinuria
        ('324281000000104'),  -- Chronic kidney disease stage 3 without proteinuria
        ('324311000000101'),  -- Chronic kidney disease stage 3A with proteinuria
        ('324341000000100'),  -- Chronic kidney disease stage 3A without proteinuria
        ('324371000000106'),  -- Chronic kidney disease stage 3B with proteinuria

        -- Malignant hypertensive CKD
        ('285871000119106'),  -- Malignant hypertensive chronic kidney disease stage 3

        -- Diabetes-related CKD
        ('771000119108')  -- Chronic kidney disease due to type 2 diabetes mellitus

        -- Note: Excluded CKD stage 1 and 2 (eGFR ≥60) as these do not require dose reduction:
        -- - 431855005 (CKD stage 1, eGFR ≥90)
        -- - 431856006 (CKD stage 2, eGFR 60-89)
    ) AS t(code)
),

high_dose_digoxin_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- These codes match actual UK prescription data
    -- Only includes digoxin formulations >125 micrograms (i.e., 250 microgram formulations)
    SELECT code FROM (VALUES
        -- Parent/international codes (substance level - for reference)
        ('387461003'),  -- Digoxin [PARENT]

        -- UK dm+d codes: Digoxin 250 microgram products (THESE MATCH PRESCRIPTIONS!)
        ('42208611000001102'),  -- Digoxin 250 microgram tablet
        ('11650611000001108'),  -- Digoxin 250micrograms/5ml oral suspension
        ('11650511000001109')   -- Digoxin 250micrograms/5ml oral solution

        -- Note: Excluded lower doses that are appropriate in renal impairment:
        -- - 42208711000001106 (Digoxin 62.5 microgram tablet)
        -- - 42208511000001101 (Digoxin 125 microgram tablet)
        -- - 11650411000001105 (Digoxin 125micrograms/5ml oral suspension)
        -- - 11650311000001103 (Digoxin 125micrograms/5ml oral solution)
        -- - 11650111000001100 (Digoxin 75micrograms/5ml oral suspension)
        -- - 11650011000001101 (Digoxin 75micrograms/5ml oral solution)
        -- - 35368011000001101 (Digoxin 50micrograms/ml oral solution)
    ) AS t(code)
),

patients_with_renal_impairment AS (
    -- Find patients with CKD stage 3+ or renal impairment diagnosis from GP events
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        MIN(ge.EventDate) as earliest_ckd_date
    FROM {gp_events_enriched} ge
    WHERE ge.SuppliedCode IN (SELECT code FROM renal_impairment_codes)
    GROUP BY ge.FK_Patient_Link_ID
),

patients_with_high_dose_digoxin AS (
    -- Find patients with renal impairment prescribed high-dose digoxin (250 mcg)
    SELECT DISTINCT
        ri.FK_Patient_Link_ID,
        p.medication_start_date as digoxin_start_date,
        p.medication_end_date as digoxin_end_date,
        p.medication_code as digoxin_code,
        p.medication_name as digoxin_name
    FROM patients_with_renal_impairment ri
    INNER JOIN {gp_prescriptions} p
        ON ri.FK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE p.medication_code IN (SELECT code FROM high_dose_digoxin_codes)
        AND p.medication_start_date >= ri.earliest_ckd_date
)

-- Return patient IDs matching this filter with period dates
SELECT DISTINCT
    FK_Patient_Link_ID,
    '003' as filter_id,
    digoxin_start_date as start_date,
    digoxin_end_date as end_date
FROM patients_with_high_dose_digoxin;
