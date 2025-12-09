-- Filter 005: Prescription of diltiazem or verapamil in a patient with heart failure
--
-- This filter identifies patients who:
-- 1. Have a recorded diagnosis of heart failure (any type)
-- 2. Have been prescribed diltiazem or verapamil (non-dihydropyridine calcium channel blockers)
--
-- Design decisions:
-- - Uses GP Events for heart failure diagnoses
-- - Uses GP Prescriptions table for medication prescriptions
-- - Includes systemic formulations only (oral tablets, capsules, solutions)
-- - Excludes topical diltiazem formulations (creams, gels, ointments) used for anal fissures
-- - Non-dihydropyridine CCBs (diltiazem, verapamil) have negative inotropic effects
-- - They can worsen heart failure by reducing cardiac contractility and worsening systolic function
-- - Dihydropyridine CCBs (amlodipine, felodipine) are safer in heart failure and excluded from this filter
-- - Prioritizes precision: only flags clear cases of contraindicated CCB use in heart failure
-- - Risk level: 3 (significant risk of heart failure decompensation)

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

diltiazem_verapamil_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- These codes match actual UK prescription data
    -- Includes ONLY systemic formulations (oral); excludes topical diltiazem
    SELECT code FROM (VALUES
        -- Parent/international codes (substance level - for reference)
        ('372913009'),  -- Diltiazem [PARENT]
        ('372754009'),  -- Verapamil [PARENT]

        -- UK dm+d codes: Diltiazem oral formulations (THESE MATCH PRESCRIPTIONS!)
        -- Modified-release capsules
        ('39023011000001107'),  -- Diltiazem 60mg modified-release capsule
        ('39023111000001108'),  -- Diltiazem 90mg modified-release capsule
        ('39023211000001102'),  -- Diltiazem 120mg modified-release capsule
        ('39023311000001105'),  -- Diltiazem 180mg modified-release capsule
        ('39023411000001103'),  -- Diltiazem 200mg modified-release capsule
        ('39023511000001104'),  -- Diltiazem 240mg modified-release capsule
        ('39023611000001100'),  -- Diltiazem 300mg modified-release capsule
        ('39023711000001109'),  -- Diltiazem 360mg modified-release capsule

        -- Modified-release tablets
        ('39023811000001101'),  -- Diltiazem 60mg modified-release tablet
        ('39023911000001106'),  -- Diltiazem 90mg modified-release tablet
        ('39024011000001109'),  -- Diltiazem 120mg modified-release tablet

        -- Oral solutions/suspensions
        ('8456811000001103'),   -- Diltiazem 90mg/5ml oral solution
        ('8457011000001107'),   -- Diltiazem 60mg/5ml oral solution
        ('8456711000001106'),   -- Diltiazem 90mg/5ml oral suspension
        ('8456911000001108'),   -- Diltiazem 60mg/5ml oral suspension
        ('12027011000001109'),  -- Diltiazem 100mg/5ml oral solution
        ('12027111000001105'),  -- Diltiazem 10mg/5ml oral solution
        ('12027311000001107'),  -- Diltiazem 120mg/5ml oral solution
        ('12027611000001102'),  -- Diltiazem 20mg/5ml oral solution
        ('12027811000001103'),  -- Diltiazem 30mg/5ml oral solution
        ('12027911000001108'),  -- Diltiazem 50mg/5ml oral solution

        -- UK dm+d codes: Verapamil oral formulations (THESE MATCH PRESCRIPTIONS!)
        -- Conventional release tablets
        ('42217311000001109'),  -- Verapamil 40mg tablet
        ('42217411000001102'),  -- Verapamil 80mg tablet
        ('42217111000001107'),  -- Verapamil 120mg tablet
        ('42217211000001101'),  -- Verapamil 160mg tablet

        -- Modified-release tablets
        ('38750211000001107'),  -- Verapamil 240mg modified-release tablet
        ('35367911000001103'),  -- Verapamil 120mg modified-release tablet

        -- Modified-release capsules
        ('39021011000001106'),  -- Verapamil 240mg modified-release capsule
        ('36565011000001105'),  -- Verapamil 120mg modified-release capsule
        ('36149411000001103'),  -- Verapamil 180mg modified-release capsule

        -- Oral solutions/suspensions
        ('12940911000001104'),  -- Verapamil 10mg/5ml oral solution
        ('12941011000001107'),  -- Verapamil 10mg/5ml oral suspension
        ('13014311000001101'),  -- Verapamil 120mg/5ml oral solution
        ('13014411000001108'),  -- Verapamil 120mg/5ml oral suspension
        ('13014511000001107'),  -- Verapamil 20mg/5ml oral solution
        ('13014611000001106'),  -- Verapamil 20mg/5ml oral suspension
        ('13014711000001102'),  -- Verapamil 240mg/5ml oral solution
        ('13014811000001105'),  -- Verapamil 240mg/5ml oral suspension
        ('13014911000001100'),  -- Verapamil 250mg/5ml oral solution
        ('13015011000001100'),  -- Verapamil 250mg/5ml oral suspension
        ('13015111000001104'),  -- Verapamil 30mg/5ml oral solution
        ('13015211000001105'),  -- Verapamil 30mg/5ml oral suspension
        ('13015311000001102'),  -- Verapamil 40mg/5ml oral solution
        ('13015411000001109'),  -- Verapamil 40mg/5ml oral suspension
        ('13015511000001108'),  -- Verapamil 45mg/5ml oral solution
        ('13015611000001107'),  -- Verapamil 45mg/5ml oral suspension
        ('13015711000001103'),  -- Verapamil 50mg/5ml oral solution
        ('13015811000001106'),  -- Verapamil 50mg/5ml oral suspension
        ('13015911000001101'),  -- Verapamil 80mg/5ml oral solution
        ('13016011000001109'),  -- Verapamil 80mg/5ml oral suspension
        ('4139411000001106')    -- Verapamil 40mg/5ml oral solution sugar free

        -- Note: Excluded topical diltiazem formulations (creams, gels, ointments)
        -- These are used for anal fissures and have minimal systemic absorption
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

patients_with_ccb AS (
    -- Find patients with heart failure prescribed diltiazem or verapamil
    SELECT DISTINCT
        hf.FK_Patient_Link_ID,
        p.medication_start_date as ccb_start_date,
        p.medication_end_date as ccb_end_date,
        p.medication_code as ccb_code,
        p.medication_name as ccb_name
    FROM patients_with_heart_failure hf
    INNER JOIN {gp_prescriptions} p
        ON hf.FK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE p.medication_code IN (SELECT code FROM diltiazem_verapamil_codes)
        AND p.medication_start_date >= hf.earliest_hf_date
)

-- Return patient IDs matching this filter with period dates
SELECT DISTINCT
    FK_Patient_Link_ID,
    5 as filter_id,
    ccb_start_date as start_date,
    ccb_end_date as end_date
FROM patients_with_ccb;
