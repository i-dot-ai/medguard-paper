-- Filter 004: Prescription of digoxin at a dose of greater than 125 mg daily for a patient with heart failure who is in sinus rhythm
--
-- This filter identifies patients who:
-- 1. Have a recorded diagnosis of heart failure (any type)
-- 2. Have evidence of sinus rhythm (normal rhythm, not atrial fibrillation)
-- 3. Have been prescribed digoxin at a dose >125 micrograms daily (i.e., 250 micrograms)
--
-- Design decisions:
-- - Uses GP Events for heart failure and sinus rhythm diagnoses/observations
-- - Uses GP Prescriptions table for medication prescriptions
-- - Note: CSV states ">125 mg" but this is a typo - digoxin is dosed in micrograms (mcg), not milligrams
-- - Sinus rhythm identified by explicit SNOMED codes for sinus rhythm/normal sinus rhythm
-- - Digoxin in heart failure is primarily used for rate control in atrial fibrillation
-- - In sinus rhythm, digoxin benefit is limited and high doses (>125 mcg) may not be needed
-- - Standard dose in sinus rhythm should be ≤125 micrograms; 250 micrograms is excessive
-- - Prioritizes precision: only flags clear cases where all three criteria are met
-- - Risk level: 3 (significant risk - limited benefit with increased toxicity risk)

WITH heart_failure_codes AS (
    -- SNOMED codes for heart failure and all descendants
    -- Based on concept_id 84114007 (Heart failure disorder)
    SELECT code FROM (VALUES
        ('84114007'),   -- Heart failure (disorder) [PARENT]
        ('42343007'),   -- Congestive heart failure (disorder)
        ('48447003'),   -- Chronic heart failure (disorder)
        ('56675007'),   -- Acute heart failure (disorder)
        ('85232009'),   -- Left heart failure (disorder)
        ('367363000'),  -- Right ventricular failure (disorder)
        ('46113002'),   -- Hypertensive heart failure (disorder)
        ('314206003'),  -- Refractory heart failure (disorder)
        ('418304008'),  -- Diastolic heart failure
        ('417996009'),  -- Systolic heart failure
        ('10091002'),   -- High output heart failure (disorder)
        ('25544003'),   -- Low output heart failure (disorder)
        ('195111005'),  -- Decompensated cardiac failure (disorder)
        ('195112003'),  -- Compensated cardiac failure (disorder)
        ('88805009'),   -- Chronic congestive heart failure (disorder)
        ('10633002'),   -- Acute congestive heart failure (disorder)
        ('111283005'),  -- Chronic left-sided heart failure (disorder)
        ('364006'),     -- Acute left-sided heart failure (disorder)
        ('10335000'),   -- Chronic right-sided heart failure (disorder)
        ('359617009'),  -- Acute right-sided heart failure (disorder)
        ('441481004'),  -- Chronic systolic heart failure (disorder)
        ('441530006'),  -- Chronic diastolic heart failure (disorder)
        ('443254009'),  -- Acute systolic heart failure
        ('443343001'),  -- Acute diastolic heart failure
        ('92506005'),   -- Biventricular congestive heart failure (disorder)
        ('44313006'),   -- Right heart failure secondary to left heart failure (disorder)
        ('703272007'),  -- Heart failure with reduced ejection fraction
        ('446221000'),  -- Heart failure with normal ejection fraction
        ('788950000'),  -- Heart failure with mid range ejection fraction
        ('5148006'),    -- Hypertensive heart disease with congestive heart failure (disorder)
        ('424404003'),  -- Decompensated chronic heart failure
        ('71892000'),   -- Cardiac asthma (disorder)
        ('195114002'),  -- Acute left ventricular failure (disorder)
        ('1296659009'), -- Acute exacerbation of chronic heart failure (disorder)
        ('698594003'),  -- Symptomatic congestive heart failure
        ('426263006'),  -- Congestive heart failure due to left ventricular systolic dysfunction
        ('426611007'),  -- Congestive heart failure due to valvular disease
        ('101281000119107'), -- Congestive heart failure due to cardiomyopathy (disorder)
        ('67431000119105'),  -- Congestive heart failure stage D (disorder)
        ('67441000119101'),  -- Congestive heart failure stage C (disorder)
        ('717840005')   -- Congestive heart failure stage B
    ) AS t(code)
),

sinus_rhythm_codes AS (
    -- SNOMED codes for sinus rhythm (normal rhythm, not atrial fibrillation)
    SELECT code FROM (VALUES
        ('251150006'),  -- Sinus rhythm (finding)
        ('64730000'),   -- Normal sinus rhythm (finding)
        ('426783006'),  -- ECG: sinus rhythm
        ('426285000'),  -- ECG: normal sinus rhythm
        ('162999005')   -- On examination - pulse rhythm regular (finding)
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

        -- Note: Excluded lower doses that are appropriate in sinus rhythm:
        -- - 42208711000001106 (Digoxin 62.5 microgram tablet)
        -- - 42208511000001101 (Digoxin 125 microgram tablet)
        -- - 11650411000001105 (Digoxin 125micrograms/5ml oral suspension)
        -- - 11650311000001103 (Digoxin 125micrograms/5ml oral solution)
    ) AS t(code)
),

patients_with_heart_failure AS (
    -- Find patients with heart failure diagnosis from GP events
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        MIN(ge.EventDate) as earliest_hf_date
    FROM {gp_events_enriched} ge
    WHERE ge.SuppliedCode IN (SELECT code FROM heart_failure_codes)
    GROUP BY ge.FK_Patient_Link_ID
),

patients_with_sinus_rhythm AS (
    -- Find patients with recorded sinus rhythm from GP events
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        MAX(ge.EventDate) as latest_sinus_rhythm_date
    FROM {gp_events_enriched} ge
    WHERE ge.SuppliedCode IN (SELECT code FROM sinus_rhythm_codes)
    GROUP BY ge.FK_Patient_Link_ID
),

patients_with_high_dose_digoxin AS (
    -- Find patients with heart failure AND sinus rhythm prescribed high-dose digoxin (250 mcg)
    SELECT DISTINCT
        hf.FK_Patient_Link_ID,
        p.medication_start_date as digoxin_start_date,
        p.medication_end_date as digoxin_end_date,
        p.medication_code as digoxin_code,
        p.medication_name as digoxin_name
    FROM patients_with_heart_failure hf
    INNER JOIN patients_with_sinus_rhythm sr
        ON hf.FK_Patient_Link_ID = sr.FK_Patient_Link_ID
    INNER JOIN {gp_prescriptions} p
        ON hf.FK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE p.medication_code IN (SELECT code FROM high_dose_digoxin_codes)
        AND p.medication_start_date >= hf.earliest_hf_date
        -- Sinus rhythm should be documented (at any time in patient history)
        -- This indicates the patient has been observed to be in sinus rhythm
)

-- Return patient IDs matching this filter with period dates
SELECT DISTINCT
    FK_Patient_Link_ID,
    '004' as filter_id,
    digoxin_start_date as start_date,
    digoxin_end_date as end_date
FROM patients_with_high_dose_digoxin;
