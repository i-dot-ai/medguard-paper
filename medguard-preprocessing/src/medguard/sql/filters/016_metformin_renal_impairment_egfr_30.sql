-- Filter 016: Metformin prescribed to a patient with renal impairment where the eGFR is ≤30 ml/min
--
-- This filter identifies patients who:
-- 1. Have a recorded eGFR measurement ≤30 ml/min OR a diagnosis of severe renal impairment (CKD stage 4-5)
-- 2. Have been prescribed metformin after or during the period of documented renal impairment
--
-- Clinical rationale:
-- - Metformin is contraindicated in patients with eGFR ≤30 ml/min due to risk of lactic acidosis
-- - UK NICE guidelines recommend discontinuing metformin when eGFR falls below 30 ml/min
-- - Risk level: HIGH - potential for life-threatening lactic acidosis
--
-- Design decisions:
-- - Uses GP Events for eGFR measurements (Value column contains numeric eGFR reading)
-- - Uses GP Events for severe renal impairment diagnoses (CKD stage 4, 5, ESRD) as backup
-- - Uses GP Prescriptions table for metformin prescriptions (consolidated prescription islands)
-- - Includes all metformin formulations: tablets, capsules, solutions, modified-release
-- - Includes combination products containing metformin (with DPP-4 inhibitors, SGLT2 inhibitors, etc.)
-- - Temporal logic: metformin prescription must start after eGFR ≤30 was recorded
-- - Looks back up to 12 months from prescription for most recent eGFR reading
-- - Prioritizes precision: only flags clear contraindication cases

WITH egfr_observation_codes AS (
    -- SNOMED codes for eGFR observations
    -- These are international codes used in GP Events for laboratory results
    SELECT code FROM (VALUES
        ('1107411000000104'),  -- Estimated glomerular filtration rate by laboratory calculation (observable entity)
        ('857971000000104'),   -- eGFR using CKD-Epi formula
        ('963621000000102'),   -- Estimated glomerular filtration rate using creatinine CKD-Epi equation
        ('963601000000106'),   -- Estimated glomerular filtration rate using cystatin C CKD-Epi equation
        ('1011481000000105'),  -- eGFR using creatinine CKD-Epi equation per 1.73 square metres
        ('1011491000000107'),  -- eGFR using cystatin C CKD-Epi equation per 1.73 square metres
        ('80274001')           -- Glomerular filtration rate (observable entity)
    ) AS t(code)
),

severe_renal_impairment_codes AS (
    -- SNOMED codes for severe renal impairment diagnoses (CKD stage 4-5, ESRD)
    -- Used as backup when eGFR measurements not available
    SELECT code FROM (VALUES
        -- CKD Stage 4 (eGFR 15-29 ml/min)
        ('431857002'),  -- Chronic kidney disease stage 4 [PARENT]
        ('721000119107'),  -- Chronic kidney disease stage 4 due to type 2 diabetes mellitus
        ('90751000119109'),  -- Chronic kidney disease stage 4 due to type 1 diabetes mellitus
        ('129151000119102'),  -- Chronic kidney disease stage 4 due to hypertension
        ('285001000119105'),  -- Chronic kidney disease stage 4 due to benign hypertension
        ('324441000000106'),  -- Chronic kidney disease stage 4 with proteinuria
        ('324471000000100'),  -- Chronic kidney disease stage 4 without proteinuria

        -- CKD Stage 5 (eGFR <15 ml/min)
        ('433146000'),  -- Chronic kidney disease stage 5 [PARENT]
        ('711000119100'),  -- Chronic kidney disease stage 5 due to type 2 diabetes mellitus
        ('90761000119106'),  -- Chronic kidney disease stage 5 due to type 1 diabetes mellitus
        ('129161000119100'),  -- Chronic kidney disease stage 5 due to hypertension
        ('285011000119108'),  -- Chronic kidney disease stage 5 due to benign hypertension
        ('714152005'),  -- Chronic kidney disease stage 5 on dialysis
        ('714153000'),  -- Chronic kidney disease stage 5 with transplant
        ('324501000000107'),  -- Chronic kidney disease stage 5 with proteinuria
        ('324541000000105'),  -- Chronic kidney disease stage 5 without proteinuria

        -- End stage renal disease
        ('46177005'),  -- End-stage renal disease [PARENT]
        ('236435004'),  -- End stage renal failure on dialysis
        ('236434000'),  -- End stage renal failure untreated by renal replacement therapy
        ('111411000119103'),  -- End stage renal disease due to hypertension
        ('90791000119104'),  -- End stage renal disease on dialysis due to type 2 diabetes mellitus
        ('90771000119100'),  -- End stage renal disease on dialysis due to type 1 diabetes mellitus

        -- Severe chronic renal failure
        ('90688005'),  -- Chronic renal failure syndrome [PARENT]
        ('723190009'),  -- Chronic renal insufficiency
        ('425369003')   -- Chronic progressive renal failure
    ) AS t(code)
),

metformin_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- These codes match actual UK prescription data
    SELECT code FROM (VALUES
        -- Parent/international codes (substance level - for reference)
        ('109081006'),  -- Metformin [PARENT]
        ('372567009'),  -- Metformin hydrochloride [PARENT]

        -- UK dm+d codes: Metformin conventional release tablets (THESE MATCH PRESCRIPTIONS!)
        ('39461411000001102'),  -- Metformin 1g conventional release tablet
        ('42085111000001105'),  -- Metformin 850mg conventional release tablet
        ('42084911000001109'),  -- Metformin 500mg conventional release tablet

        -- UK dm+d codes: Metformin modified-release tablets
        ('38893711000001104'),  -- Metformin 1g modified-release tablet
        ('43146111000001106'),  -- Metformin 850mg modified-release tablet
        ('38893811000001107'),  -- Metformin 750mg modified-release tablet
        ('39113511000001101'),  -- Metformin 500mg modified-release tablet

        -- UK dm+d codes: Metformin oral solutions and suspensions
        ('42085011000001109'),  -- Metformin 500mg/5ml oral solution
        ('8664111000001107'),   -- Metformin 425mg/5ml oral solution
        ('8663911000001108'),   -- Metformin 250mg/5ml oral solution
        ('8664211000001101'),   -- Metformin 425mg/5ml oral suspension
        ('8664011000001106'),   -- Metformin 250mg/5ml oral suspension
        ('8664411000001102'),   -- Metformin 500mg/5ml oral suspension
        ('8664611000001104'),   -- Metformin 850mg/5ml oral solution
        ('8664711000001108'),   -- Metformin 850mg/5ml oral suspension
        ('12798011000001101'),  -- Metformin 1g/5ml oral solution
        ('12813711000001107'),  -- Metformin 5mg/5ml oral solution
        ('10750111000001100'),  -- Metformin 500mg/5ml oral solution sugar free
        ('33550811000001105'),  -- Metformin 1g/5ml oral solution sugar free
        ('33550911000001100'),  -- Metformin 850mg/5ml oral solution sugar free

        -- UK dm+d codes: Metformin capsules
        ('8796711000001107'),   -- Metformin 850mg capsules

        -- UK dm+d codes: Metformin powder sachets
        ('15411311000001103'),  -- Metformin 500mg oral powder sachets sugar free
        ('15411211000001106'),  -- Metformin 1g oral powder sachets sugar free

        -- UK dm+d codes: Metformin combination products
        -- With DPP-4 inhibitors
        ('45270811000001109'),  -- Metformin 850mg + Sitagliptin 50mg tablet
        ('17071811000001108'),  -- Metformin 1g + Sitagliptin 50mg tablet
        ('13413111000001109'),  -- Vildagliptin 50mg + Metformin 850mg tablet
        ('13413011000001108'),  -- Vildagliptin 50mg + Metformin 1g tablet
        ('21245111000001107'),  -- Linagliptin 2.5mg + Metformin 850mg tablet
        ('21245011000001106'),  -- Linagliptin 2.5mg + Metformin 1g tablet
        ('21711511000001101'),  -- Saxagliptin 2.5mg + Metformin 850mg tablet
        ('21711411000001100'),  -- Saxagliptin 2.5mg + Metformin 1g tablet
        ('23637211000001102'),  -- Alogliptin 12.5mg + Metformin 1g tablet

        -- With SGLT2 inhibitors
        ('30318311000001106'),  -- Empagliflozin 5mg + Metformin 1g tablet
        ('30318411000001104'),  -- Empagliflozin 5mg + Metformin 850mg tablet
        ('30318111000001109'),  -- Empagliflozin 12.5mg + Metformin 1g tablet
        ('30318211000001103'),  -- Empagliflozin 12.5mg + Metformin 850mg tablet
        ('28049211000001101'),  -- Canagliflozin 50mg + Metformin 1g tablet
        ('28049311000001109'),  -- Canagliflozin 50mg + Metformin 850mg tablet
        ('24054611000001100'),  -- Dapagliflozin 5mg + Metformin 1g tablet
        ('24054711000001109'),  -- Dapagliflozin 5mg + Metformin 850mg tablet

        -- With glitazones (historical - mostly discontinued)
        ('42088811000001107'),  -- Metformin 1g + Rosiglitazone 2mg tablet
        ('42089011000001106'),  -- Metformin 1g + Rosiglitazone 4mg tablet
        ('42088911000001102'),  -- Metformin 500mg + Rosiglitazone 2mg tablet
        ('42088711000001104'),  -- Metformin 500mg + Rosiglitazone 1mg tablet
        ('42086111000001104')   -- Metformin 850mg + Pioglitazone 15mg tablet
    ) AS t(code)
),

patients_with_low_egfr AS (
    -- Identify patients with eGFR ≤30 ml/min from laboratory results
    -- Value column contains the numeric eGFR reading
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        ge.EventDate as egfr_date,
        TRY_CAST(ge.Value AS DOUBLE) as egfr_value
    FROM {gp_events_enriched} ge
    WHERE ge.SuppliedCode IN (SELECT code FROM egfr_observation_codes)
        AND ge.Value IS NOT NULL
        AND ge.EventDate IS NOT NULL
        -- Try to cast Value to numeric and check if ≤30
        AND TRY_CAST(ge.Value AS DOUBLE) IS NOT NULL
        AND TRY_CAST(ge.Value AS DOUBLE) > 0  -- Exclude invalid/zero values
        AND TRY_CAST(ge.Value AS DOUBLE) <= 30  -- eGFR ≤30 ml/min
),

patients_with_severe_ckd_diagnosis AS (
    -- Identify patients with documented severe renal impairment diagnoses
    -- Used as backup when eGFR measurements not available
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        ge.EventDate as diagnosis_date
    FROM {gp_events_enriched} ge
    WHERE ge.SuppliedCode IN (SELECT code FROM severe_renal_impairment_codes)
        AND ge.EventDate IS NOT NULL
),

patients_with_renal_impairment AS (
    -- Combine both sources of renal impairment evidence
    -- Use most recent date for each patient
    SELECT
        FK_Patient_Link_ID,
        MAX(renal_impairment_date) as most_recent_renal_impairment_date,
        MAX(source_type) as source_type
    FROM (
        SELECT
            FK_Patient_Link_ID,
            egfr_date as renal_impairment_date,
            'eGFR measurement' as source_type
        FROM patients_with_low_egfr

        UNION ALL

        SELECT
            FK_Patient_Link_ID,
            diagnosis_date as renal_impairment_date,
            'CKD diagnosis' as source_type
        FROM patients_with_severe_ckd_diagnosis
    ) combined
    GROUP BY FK_Patient_Link_ID
),

metformin_prescriptions AS (
    -- Find metformin prescriptions
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        p.medication_start_date,
        p.medication_end_date,
        p.medication_code,
        p.medication_name
    FROM {gp_prescriptions} p
    WHERE p.medication_code IN (SELECT code FROM metformin_codes)
        AND p.medication_start_date IS NOT NULL
),

contraindicated_prescriptions AS (
    -- Match metformin prescriptions with documented renal impairment
    -- Prescription must start after renal impairment was documented
    -- Or renal impairment must have been documented within previous 12 months
    SELECT DISTINCT
        mp.FK_Patient_Link_ID,
        mp.medication_start_date,
        mp.medication_end_date,
        mp.medication_name,
        pri.most_recent_renal_impairment_date,
        pri.source_type
    FROM metformin_prescriptions mp
    INNER JOIN patients_with_renal_impairment pri
        ON mp.FK_Patient_Link_ID = pri.FK_Patient_Link_ID
    WHERE pri.most_recent_renal_impairment_date <= mp.medication_start_date
        -- Renal impairment must be documented within 12 months before prescription
        AND pri.most_recent_renal_impairment_date >= (mp.medication_start_date - INTERVAL '365 days')
)

-- Return patient IDs matching this filter with period dates
SELECT DISTINCT
    FK_Patient_Link_ID,
    16 as filter_id,
    medication_start_date as start_date,
    medication_end_date as end_date
FROM contraindicated_prescriptions;
