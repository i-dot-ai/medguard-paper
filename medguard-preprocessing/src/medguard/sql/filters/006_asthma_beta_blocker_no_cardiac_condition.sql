-- Filter 006: Prescription of a beta-blocker to a patient with asthma (excluding patients who also have a cardiac condition, where the benefits of beta-blockers may outweigh the risks)
--
-- This filter identifies patients who:
-- 1. Have a recorded diagnosis of asthma (any type)
-- 2. Do NOT have any recorded cardiac condition (heart failure, CHD, arrhythmia, etc.)
-- 3. Have been prescribed a beta blocker after their asthma diagnosis
--
-- Design decisions:
-- - Uses GP Events for asthma and cardiac diagnoses
-- - Uses GP Prescriptions table for medication prescriptions (consolidated prescription islands)
-- - Beta blockers are contraindicated in asthma (bronchoconstriction risk)
-- - However, in cardiac conditions (AF, heart failure, post-MI), beta blocker benefits may outweigh risks
-- - Excludes patients with ANY cardiac condition where beta blockers might be indicated
-- - Cardiac conditions include: ischaemic heart disease, heart failure, arrhythmias, cardiomyopathy, valve disease
-- - Prioritizes precision: only flags clear cases where beta blocker use in asthma has no cardiac justification
-- - Risk level: 3 (significant risk of bronchoconstriction)

WITH asthma_codes AS (
    -- SNOMED codes for asthma and all descendants
    SELECT code FROM (VALUES
        ('195967001'),  -- Asthma (disorder) [PARENT]
        ('225057002'),  -- Brittle asthma (disorder)
        ('233679003'),  -- Late onset asthma (disorder)
        ('266361008'),  -- Non-allergic asthma (disorder)
        ('281239006'),  -- Acute asthma
        ('55570000'),   -- Asthma without status asthmaticus (disorder)
        ('93432008'),   -- Drug-induced asthma (disorder)
        ('195977004'),  -- Mixed asthma (disorder)
        ('233678006'),  -- Childhood asthma (disorder)
        ('405944004'),  -- Asthmatic bronchitis
        ('409663006'),  -- Cough variant asthma
        ('389145006'),  -- Allergic asthma
        ('370218001'),  -- Mild asthma (disorder)
        ('370219009'),  -- Moderate asthma (disorder)
        ('370220003'),  -- Occasional asthma (disorder)
        ('370221004'),  -- Severe asthma (disorder)
        ('92807009'),   -- Chemical-induced asthma (disorder)
        ('427603009'),  -- Intermittent asthma
        ('445427006'),  -- Seasonal asthma
        ('57607007'),   -- Occupational asthma (disorder)
        ('401000119107'), -- Asthma with irreversible airway obstruction
        ('707444001'),  -- Uncomplicated asthma (disorder)
        ('10692761000119107'), -- Asthma-COPD overlap syndrome
        ('2360001000004109'), -- Steroid dependent asthma (disorder)
        ('72301000119103'), -- Asthma in pregnancy
        ('233691007'),  -- Asthmatic pulmonary eosinophilia (disorder)
        ('1290026000'),  -- Uncontrolled asthma
        ('12428000'),   -- Intrinsic asthma without status asthmaticus
        ('63088003'),   -- Allergic asthma without status asthmaticus
        ('195949008'),  -- Chronic asthmatic bronchitis (disorder)
        ('424643009'),  -- IgE-mediated allergic asthma
        ('423889005'),  -- Non-IgE mediated allergic asthma
        ('427679007'),  -- Mild intermittent asthma
        ('426979002'),  -- Mild persistent asthma
        ('427295004'),  -- Moderate persistent asthma
        ('426656000')   -- Severe persistent asthma
    ) AS t(code)
),

cardiac_condition_codes AS (
    -- SNOMED codes for cardiac conditions where beta blockers may be indicated
    -- Exclusion criteria: patients with these conditions are NOT flagged
    SELECT code FROM (VALUES
        -- Ischaemic heart disease (CHD, MI, angina)
        ('414545008'),  -- Ischaemic heart disease [PARENT]
        ('53741008'),   -- Coronary arteriosclerosis (disorder)
        ('22298006'),   -- Myocardial infarction (disorder)
        ('194828000'),  -- Angina (disorder)
        ('413838009'),  -- Chronic ischaemic heart disease
        ('413439005'),  -- Acute ischaemic heart disease

        -- Heart failure (all types)
        ('84114007'),   -- Heart failure (disorder) [PARENT]
        ('42343007'),   -- Congestive heart failure (disorder)
        ('48447003'),   -- Chronic heart failure (disorder)
        ('56675007'),   -- Acute heart failure (disorder)
        ('85232009'),   -- Left heart failure (disorder)
        ('367363000'),  -- Right ventricular failure (disorder)
        ('418304008'),  -- Diastolic heart failure
        ('417996009'),  -- Systolic heart failure
        ('88805009'),   -- Chronic congestive heart failure
        ('703272007'),  -- Heart failure with reduced ejection fraction
        ('446221000'),  -- Heart failure with normal ejection fraction

        -- Cardiac arrhythmias
        ('698247007'),  -- Cardiac arrhythmia [PARENT]
        ('49436004'),   -- Atrial fibrillation (disorder)
        ('5370000'),    -- Atrial flutter (disorder)
        ('72724002'),   -- Supraventricular tachycardia (disorder)
        ('25569003'),   -- Ventricular tachycardia (disorder)
        ('282825002'),  -- Paroxysmal atrial fibrillation (disorder)
        ('426749004'),  -- Chronic atrial fibrillation
        ('440059007'),  -- Persistent atrial fibrillation
        ('440028005'),  -- Permanent atrial fibrillation
        ('6456007'),    -- Supraventricular arrhythmia (finding)
        ('44103008'),   -- Ventricular arrhythmia

        -- Cardiomyopathy
        ('57809008'),   -- Myocardial disease (disorder)
        ('399020009'),  -- Dilated cardiomyopathy
        ('233873004'),  -- Hypertrophic cardiomyopathy

        -- Valvular heart disease
        ('368009'),     -- Heart valve disorder (disorder)
        ('40445007'),   -- Heart valve regurgitation (disorder)
        ('44241007'),   -- Heart valve stenosis (disorder)

        -- Hypertensive heart disease
        ('64715009'),   -- Hypertensive heart disease (disorder)
        ('46113002'),   -- Hypertensive heart failure (disorder)
        ('5148006')     -- Hypertensive heart disease with congestive heart failure

        -- Note: This list is deliberately comprehensive to ensure we don't flag
        -- patients where beta blockers may have cardiovascular benefits
    ) AS t(code)
),

beta_blocker_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- These codes match actual UK prescription data
    SELECT code FROM (VALUES
        -- Parent/international codes (substance level - for reference)
        ('373254001'),  -- Beta blocker [PARENT]
        ('372772003'),  -- Propranolol
        ('387506000'),  -- Atenolol
        ('372826007'),  -- Metoprolol
        ('386868003'),  -- Bisoprolol
        ('386870007'),  -- Carvedilol
        ('372911006'),  -- Sotalol
        ('387482003'),  -- Nadolol
        ('395808005'),  -- Nebivolol
        ('372750000'),  -- Labetalol

        -- UK dm+d codes: Propranolol products (THESE MATCH PRESCRIPTIONS!)
        ('42380211000001107'),  -- Propranolol 160mg tablet
        ('42380511000001105'),  -- Propranolol 80mg tablet
        ('42380311000001104'),  -- Propranolol 40mg tablet
        ('42380111000001101'),  -- Propranolol 10mg tablet
        ('38751111000001107'),  -- Propranolol 80mg modified-release capsule
        ('38751211000001101'),  -- Propranolol 160mg modified-release capsule
        ('8672811000001103'),   -- Propranolol 40mg/5ml oral suspension
        ('8672911000001108'),   -- Propranolol 80mg/5ml oral solution

        -- UK dm+d codes: Atenolol products
        ('42370411000001101'),  -- Atenolol 100mg tablet
        ('42370611000001103'),  -- Atenolol 25mg tablet
        ('42370711000001107'),  -- Atenolol 50mg tablet

        -- UK dm+d codes: Metoprolol products
        ('39992211000001108'),  -- Metoprolol 25mg tablet
        ('42377311000001109'),  -- Metoprolol 100mg tablet
        ('42377411000001102'),  -- Metoprolol 50mg tablet

        -- UK dm+d codes: Bisoprolol products
        ('42371511000001109'),  -- Bisoprolol 5mg tablet
        ('42371211000001106'),  -- Bisoprolol 10mg tablet
        ('42371311000001103'),  -- Bisoprolol 2.5mg tablet
        ('42371411000001105'),  -- Bisoprolol 3.75mg tablet
        ('42371611000001108'),  -- Bisoprolol 7.5mg tablet
        ('42371111000001100'),  -- Bisoprolol 1.25mg tablet

        -- UK dm+d codes: Carvedilol products
        ('42372611000001102'),  -- Carvedilol 25mg tablet
        ('42372711000001106'),  -- Carvedilol 3.125mg tablet
        ('42372811000001103'),  -- Carvedilol 6.25mg tablet
        ('42372511000001101'),  -- Carvedilol 12.5mg tablet

        -- UK dm+d codes: Sotalol products
        ('42382611000001105'),  -- Sotalol 40mg tablet
        ('42382511000001106'),  -- Sotalol 200mg tablet
        ('42382411000001107'),  -- Sotalol 160mg tablet
        ('42382711000001101'),  -- Sotalol 80mg tablet

        -- UK dm+d codes: Nebivolol products
        ('39701011000001101'),  -- Nebivolol 10mg tablet
        ('39701211000001106'),  -- Nebivolol 5mg tablet
        ('38659211000001107'),  -- Nebivolol 1.25mg tablet
        ('39701111000001100'),  -- Nebivolol 2.5mg tablet

        -- UK dm+d codes: Labetalol products
        ('42375811000001105'),  -- Labetalol 200mg tablet
        ('42375711000001102'),  -- Labetalol 100mg tablet
        ('42375911000001100'),  -- Labetalol 400mg tablet
        ('42376011000001108'),  -- Labetalol 50mg tablet

        -- UK dm+d codes: Nadolol products
        ('42377811000001100'),  -- Nadolol 40mg tablet
        ('42378011000001107')   -- Nadolol 80mg tablet
    ) AS t(code)
),

patients_with_asthma AS (
    -- Find patients with asthma diagnosis from GP events
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        MIN(ge.EventDate) as earliest_asthma_date
    FROM {gp_events_enriched} ge
    WHERE ge.SuppliedCode IN (SELECT code FROM asthma_codes)
    GROUP BY ge.FK_Patient_Link_ID
),

patients_with_cardiac_condition AS (
    -- Find patients with any cardiac condition
    -- These patients will be EXCLUDED from the filter
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        MIN(ge.EventDate) as earliest_cardiac_date
    FROM {gp_events_enriched} ge
    WHERE ge.SuppliedCode IN (SELECT code FROM cardiac_condition_codes)
    GROUP BY ge.FK_Patient_Link_ID
),

patients_asthma_no_cardiac AS (
    -- Find patients with asthma but NO cardiac condition
    SELECT
        pa.FK_Patient_Link_ID,
        pa.earliest_asthma_date
    FROM patients_with_asthma pa
    LEFT JOIN patients_with_cardiac_condition pc
        ON pa.FK_Patient_Link_ID = pc.FK_Patient_Link_ID
    WHERE pc.FK_Patient_Link_ID IS NULL  -- Exclude patients with any cardiac condition
),

patients_with_beta_blocker AS (
    -- Find patients prescribed beta blockers after asthma diagnosis
    -- Only include patients without cardiac conditions
    SELECT DISTINCT
        panc.FK_Patient_Link_ID,
        p.medication_start_date as beta_blocker_start_date,
        p.medication_end_date as beta_blocker_end_date,
        p.medication_code as beta_blocker_code,
        p.medication_name as beta_blocker_name
    FROM patients_asthma_no_cardiac panc
    INNER JOIN {gp_prescriptions} p
        ON panc.FK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE p.medication_code IN (SELECT code FROM beta_blocker_codes)
        AND p.medication_start_date >= panc.earliest_asthma_date
)

-- Return patient IDs matching this filter with period dates
SELECT DISTINCT
    FK_Patient_Link_ID,
    6 as filter_id,
    beta_blocker_start_date as start_date,
    beta_blocker_end_date as end_date
FROM patients_with_beta_blocker;
