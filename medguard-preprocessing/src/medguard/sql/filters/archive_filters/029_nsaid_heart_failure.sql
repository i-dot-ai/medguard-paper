-- Filter 029: Prescription of an NSAID in a patient with heart failure
-- Description: NSAID prescribed to patient with a diagnosis of heart failure
-- Category: Contraindicated medication
-- Risk level: 3
--
-- This filter identifies patients who:
-- 1. Have a recorded diagnosis of heart failure
-- 2. Have been prescribed an NSAID after their heart failure diagnosis
--
-- Rationale:
-- - NSAIDs can cause fluid retention and worsen heart failure
-- - NSAIDs reduce the efficacy of diuretics and ACE inhibitors
-- - NSAIDs increase risk of hospitalization and mortality in HF patients
-- - NSAIDs are relatively contraindicated in heart failure (BNF caution)
--
-- Design decisions:
-- - Uses GP Events for heart failure diagnosis
-- - Includes all NSAIDs (ibuprofen, naproxen, diclofenac, etc.)
-- - Excludes selective COX-2 inhibitors (separately managed, also contraindicated but different risk profile)
-- - NSAID prescription must occur after heart failure diagnosis
-- - Includes both oral and topical NSAIDs (topical can have systemic effects)

WITH heart_failure_codes AS (
    -- Reused from filter 015
    SELECT code FROM (VALUES
        -- Heart failure diagnoses
        ('84114007'),   -- Heart failure (disorder)
        ('42343007'),   -- Congestive heart failure (disorder)
        ('48447003'),   -- Chronic heart failure (disorder)
        ('56675007'),   -- Acute heart failure (disorder)
        ('85232009'),   -- Left heart failure (disorder)
        ('367363000'),  -- Right ventricular failure (disorder)
        ('44313006'),   -- Right heart failure secondary to left heart failure (disorder)
        ('23341000119109'), -- Congestive heart failure with right heart failure (disorder)
        ('46113002'),   -- Hypertensive heart failure (disorder)
        ('314206003'),  -- Refractory heart failure (disorder)
        ('418304008'),  -- Diastolic heart failure
        ('417996009'),  -- Systolic heart failure
        ('462172006'),  -- Fetal heart failure
        ('898208007'),  -- Heart failure due to thyrotoxicosis
        ('10091002'),   -- High output heart failure (disorder)
        ('10633002'),   -- Acute congestive heart failure (disorder)
        ('25544003'),   -- Low output heart failure (disorder)
        ('82523003'),   -- Congestive rheumatic heart failure (disorder)
        ('88805009'),   -- Chronic congestive heart failure (disorder)
        ('92506005'),   -- Biventricular congestive heart failure (disorder)
        ('364006'),     -- Acute left-sided heart failure (disorder)
        ('424404003'),  -- Decompensated chronic heart failure
        ('161505003'),  -- History of heart failure (situation)
        ('395105005')   -- Heart failure confirmed (situation)
    ) AS t(code)
),

nsaid_codes AS (
    -- Reused from filter 028
    -- SNOMED codes for NSAIDs (non-selective only, excluding COX-2 inhibitors)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    SELECT code FROM (VALUES
        -- Parent/international codes (substance level)
        ('372665008'),  -- Non-steroidal anti-inflammatory agent (parent)
        ('387207008'),  -- Ibuprofen
        ('372588000'),  -- Naproxen
        ('7034005'),    -- Diclofenac
        ('373513008'),  -- Indometacin
        ('387153005'),  -- Piroxicam
        ('387185008'),  -- Mefenamic acid
        ('386832008'),  -- Ketoprofen
        ('373506008'),  -- Flurbiprofen
        ('387513000'),  -- Sulindac
        ('391703003'),  -- Aceclofenac

        -- UK dm+d codes: Ibuprofen products
        ('42104911000001104'),  -- Ibuprofen 400mg tablet
        ('42104811000001109'),  -- Ibuprofen 200mg tablet
        ('42104711000001101'),  -- Ibuprofen 200mg capsule
        ('42105311000001101'),  -- Ibuprofen 600mg tablet
        ('42105411000001108'),  -- Ibuprofen 800mg tablet
        ('42105011000001104'),  -- Ibuprofen 5% foam
        ('41740811000001103'),  -- Ibuprofen 5% gel
        ('41740611000001102'),  -- Ibuprofen 10% gel
        ('41901911000001104'),  -- Ibuprofen 5% cream
        ('42105111000001103'),  -- Ibuprofen 50mg/ml spray
        ('10774611000001104'),  -- Ibuprofen 400mg capsules

        -- UK dm+d codes: Naproxen products
        ('42107811000001100'),  -- Naproxen 500mg tablet
        ('42107511000001103'),  -- Naproxen 250mg tablet
        ('42107711000001108'),  -- Naproxen 500mg suppository
        ('42107911000001105'),  -- Naproxen sodium 275mg tablet
        ('36030111000001106'),  -- Naproxen 500mg modified-release tablets

        -- UK dm+d codes: Diclofenac products
        ('42101711000001104'),  -- Diclofenac potassium 50mg tablet
        ('42101611000001108'),  -- Diclofenac potassium 25mg tablet
        ('42101511000001109'),  -- Diclofenac sodium 50mg suppository
        ('42101411000001105'),  -- Diclofenac sodium 25mg suppository
        ('42101311000001103'),  -- Diclofenac sodium 100mg suppository
        ('37899411000001100'),  -- Diclofenac sodium 1% gel
        ('41738811000001101'),  -- Diclofenac sodium 3% gel

        -- UK dm+d codes: Indometacin products
        ('42105811000001105'),  -- Indometacin 50mg capsule
        ('42105611000001106'),  -- Indometacin 25mg capsule
        ('42105511000001107'),  -- Indometacin 100mg suppository
        ('39024911000001108'),  -- Indometacin 25mg modified-release capsule
        ('42105711000001102'),  -- Indometacin 25mg/5ml oral suspension
        ('8561611000001108'),   -- Indometacin 25mg/5ml oral solution
        ('8561811000001107'),   -- Indometacin 50mg/5ml oral solution
        ('8561911000001102'),   -- Indometacin 50mg/5ml oral suspension

        -- UK dm+d codes: Piroxicam products
        ('42110211000001103'),  -- Piroxicam 20mg capsule
        ('42110111000001109'),  -- Piroxicam 10mg capsule
        ('42110311000001106'),  -- Piroxicam 20mg suppository
        ('39721211000001103'),  -- Piroxicam 20mg tablet for suspension
        ('39721011000001108'),  -- Piroxicam 10mg tablet for suspension
        ('41743811000001105'),  -- Piroxicam 0.5% gel
        ('3439011000001103'),   -- Piroxicam betadex 20mg tablets

        -- UK dm+d codes: Mefenamic acid products
        ('42106311000001106'),  -- Mefenamic acid 250mg capsule
        ('42106411000001104'),  -- Mefenamic acid 500mg tablet
        ('41391311000001107'),  -- Mefenamic acid 250mg tablet
        ('8662311000001102'),   -- Mefenamic acid 250mg/5ml oral suspension
        ('8662411000001109'),   -- Mefenamic acid 500mg/5ml oral suspension

        -- UK dm+d codes: Ketoprofen products
        ('42106011000001108'),  -- Ketoprofen 50mg capsule
        ('42105911000001100'),  -- Ketoprofen 100mg suppository
        ('3377811000001108'),   -- Ketoprofen 100mg capsules
        ('34447711000001108'),  -- Ketoprofen 10% gel
        ('41741511000001108'),  -- Ketoprofen 2.5% gel

        -- UK dm+d codes: Flurbiprofen products
        ('42104311000001100'),  -- Flurbiprofen 50mg tablet
        ('42104211000001108'),  -- Flurbiprofen 100mg tablet
        ('42104111000001102'),  -- Flurbiprofen 100mg suppository
        ('42104411000001107'),  -- Flurbiprofen 8.75mg lozenge
        ('45332211000001104'),  -- Flurbiprofen 8.75mg lozenge sugar free

        -- UK dm+d codes: Aceclofenac products
        ('42099211000001100'),  -- Aceclofenac 100mg tablet

        -- UK dm+d codes: Sulindac products
        ('42111711000001102'),  -- Sulindac 200mg tablet
        ('42111611000001106')   -- Sulindac 100mg tablet
    ) AS t(code)
),

heart_failure_diagnoses AS (
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        ge.EventDate AS diagnosis_date
    FROM {gp_events_enriched} ge
    INNER JOIN heart_failure_codes hfc ON CAST(ge.SuppliedCode AS VARCHAR) = hfc.code
    WHERE ge.EventDate IS NOT NULL
),

nsaid_prescriptions AS (
    SELECT DISTINCT
        gp.FK_Patient_Link_ID,
        gp.medication_start_date,
        gp.medication_end_date,
        gp.medication_name
    FROM {gp_prescriptions} gp
    INNER JOIN nsaid_codes nc ON gp.medication_code = nc.code
    WHERE gp.medication_start_date IS NOT NULL
),

contraindicated_prescriptions AS (
    SELECT DISTINCT
        np.FK_Patient_Link_ID,
        np.medication_start_date,
        np.medication_end_date,
        np.medication_name,
        hfd.diagnosis_date
    FROM nsaid_prescriptions np
    INNER JOIN heart_failure_diagnoses hfd
        ON np.FK_Patient_Link_ID = hfd.FK_Patient_Link_ID
    -- NSAID prescription occurred after heart failure diagnosis (or same day)
    WHERE np.medication_start_date >= hfd.diagnosis_date
)

SELECT DISTINCT
    FK_Patient_Link_ID,
    '029' AS filter_id,
    medication_start_date AS start_date,
    medication_end_date AS end_date
FROM contraindicated_prescriptions
ORDER BY FK_Patient_Link_ID, medication_start_date;
