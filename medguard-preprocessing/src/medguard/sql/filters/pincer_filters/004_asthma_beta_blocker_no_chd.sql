-- Filter 004: Patients with asthma (and no history of coronary heart disease) who have been prescribed a beta blocker
--
-- This filter identifies patients who:
-- 1. Have a recorded diagnosis of asthma (any type)
-- 2. Do NOT have a history of coronary heart disease (CHD), myocardial infarction (MI), or angina
-- 3. Have been prescribed a beta blocker medication after their asthma diagnosis
--
-- Design decisions:
-- - Uses GP Events for asthma and CHD diagnoses
-- - Uses GP Prescriptions table for medication prescriptions (consolidated prescription islands)
-- - Beta blockers are generally contraindicated in asthma (bronchoconstriction risk)
-- - However, beta blockers may be appropriate in asthma patients with CHD (cardioprotective benefit outweighs risk)
-- - This filter focuses on patients WITHOUT CHD where beta blocker use is less clearly indicated
-- - CHD exclusion includes coronary arteriosclerosis, myocardial infarction, and angina (all types)
-- - Prioritizes precision: only flags clear cases of beta blocker prescription after asthma diagnosis in patients without CHD

WITH asthma_codes AS (
    -- SNOMED codes for asthma and all descendants
    -- Based on concept_id 195967001 (Asthma (disorder))
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
        ('401000119107'), -- Asthma with irreversible airway obstruction (disorder)
        ('707444001'),  -- Uncomplicated asthma (disorder)
        ('10692761000119107'), -- Asthma-COPD overlap syndrome
        ('2360001000004109'), -- Steroid dependent asthma (disorder)
        ('72301000119103'), -- Asthma in pregnancy
        ('233691007'),  -- Asthmatic pulmonary eosinophilia (disorder)
        ('1290026000'),  -- Uncontrolled asthma
        ('12428000'),   -- Intrinsic asthma without status asthmaticus (disorder)
        ('63088003'),   -- Allergic asthma without status asthmaticus (disorder)
        ('195949008'),  -- Chronic asthmatic bronchitis (disorder)
        ('424643009'),  -- IgE-mediated allergic asthma (disorder)
        ('423889005'),  -- Non-IgE mediated allergic asthma (disorder)
        ('56968009'),   -- Asthma caused by wood dust
        ('233687002'),  -- Colophony asthma (disorder)
        ('703953004'),  -- Allergic asthma caused by D. pteronyssinus
        ('703954005'),  -- Allergic asthma caused by D. farinae
        ('427679007'),  -- Mild intermittent asthma
        ('426979002'),  -- Mild persistent asthma
        ('427295004'),  -- Moderate persistent asthma
        ('426656000'),  -- Severe persistent asthma
        ('786836003'),  -- Near fatal asthma
        ('404804003'),  -- Platinum asthma
        ('404808000'),  -- Isocyanate induced asthma
        ('233688007'),  -- Sulfite-induced asthma (disorder)
        ('233683003'),  -- Hay fever with asthma (disorder)
        ('18041002'),   -- Printers' asthma (disorder)
        ('19849005'),   -- Meat-wrappers' asthma (disorder)
        ('34015007'),   -- Bakers' asthma (disorder)
        ('404806001'),  -- Cheese-makers' asthma
        ('418395004'),  -- Tea-makers' asthma
        ('11641008'),   -- Millers' asthma (disorder)
        ('41553006'),   -- Detergent asthma (disorder)
        ('59786004')    -- Weavers' cough (disorder)
    ) AS t(code)
),

chd_codes AS (
    -- SNOMED codes for coronary heart disease, myocardial infarction, and angina
    -- These are EXCLUSION criteria - patients with any of these codes will be excluded from the filter
    SELECT code FROM (VALUES
        -- Coronary arteriosclerosis (53741008) and key descendants
        ('53741008'),   -- Coronary arteriosclerosis (disorder) [PARENT]
        ('443502000'),  -- Coronary atherosclerosis
        ('194842008'),  -- Single coronary vessel disease (disorder)
        ('194843003'),  -- Double coronary vessel disease (disorder)
        ('233817007'),  -- Triple vessel disease of the heart (disorder)
        ('371803003'),  -- Multi vessel coronary artery disease
        ('371804009'),  -- Left main coronary artery disease
        ('315348000'),  -- Asymptomatic coronary heart disease (disorder)
        ('92517006'),   -- Calcific coronary arteriosclerosis (disorder)
        ('420006002'),  -- Obliterative coronary artery disease
        ('429673002'),  -- Arteriosclerosis of coronary artery bypass graft (disorder)
        ('1293192009'), -- Premature coronary artery disease (disorder)
        ('810681000000101'), -- Coronary microvascular disease
        ('719678003'),  -- Non-obstructive atherosclerosis of coronary artery
        ('1303693000'), -- Atherosclerosis of right coronary artery
        ('1366500000'), -- Atherosclerosis of left coronary artery (disorder)
        ('1366495003'), -- Atherosclerosis of circumflex branch of left coronary artery (disorder)
        ('1366496002'), -- Atherosclerosis of left coronary artery main stem
        ('1366498001'), -- Atherosclerosis of anterior descending branch of left coronary artery (disorder)

        -- Myocardial infarction (22298006) and key descendants
        ('22298006'),   -- Myocardial infarction (disorder) [PARENT]
        ('57054005'),   -- Acute myocardial infarction (disorder)
        ('1755008'),    -- Old myocardial infarction (disorder)
        ('233843008'),  -- Silent myocardial infarction (disorder)
        ('194856005'),  -- Subsequent myocardial infarction (disorder)
        ('399211009'),  -- History of myocardial infarction (situation)
        ('401303003'),  -- Acute ST segment elevation myocardial infarction
        ('401314000'),  -- Acute non-ST segment elevation myocardial infarction
        ('314207007'),  -- Non-Q wave myocardial infarction (disorder)
        ('304914007'),  -- Acute Q wave myocardial infarction (disorder)
        ('54329005'),   -- Acute myocardial infarction of anterior wall (disorder)
        ('73795002'),   -- Acute myocardial infarction of inferior wall (disorder)
        ('58612006'),   -- Acute myocardial infarction of lateral wall (disorder)
        ('70422006'),   -- Acute subendocardial infarction (disorder)
        ('233839009'),  -- Old anterior myocardial infarction (disorder)
        ('233840006'),  -- Old inferior myocardial infarction (disorder)
        ('233841005'),  -- Old lateral myocardial infarction (disorder)
        ('233842003'),  -- Old posterior myocardial infarction (disorder)
        ('129574000'),  -- Postoperative myocardial infarction (disorder)
        ('428196007'),  -- Mixed myocardial ischemia and infarction
        ('879955009'),  -- Myocardial infarction with non-obstructive coronary artery
        ('32574007'),   -- Past myocardial infarction diagnosed on electrocardiogram

        -- Angina (194828000) and key descendants
        ('194828000'),  -- Angina (disorder) [PARENT]
        ('233819005'),  -- Stable angina (disorder)
        ('4557003'),    -- Preinfarction syndrome (disorder) [unstable angina]
        ('194823009'),  -- Acute coronary insufficiency (disorder)
        ('300995000'),  -- Exercise-induced angina (disorder)
        ('315025001'),  -- Refractory angina (disorder)
        ('371806006'),  -- Progressive angina
        ('371807002'),  -- Atypical angina
        ('429559004'),  -- Typical angina
        ('233821000'),  -- New onset angina (disorder)
        ('314116003'),  -- Post infarct angina (disorder)
        ('19057007'),   -- Status anginosus (disorder)
        ('35928006'),   -- Nocturnal angina (disorder)
        ('59021001'),   -- Angina decubitus (disorder)
        ('87343002'),   -- Prinzmetal angina (disorder)
        ('61490001'),   -- Angina, class I (disorder)
        ('41334000'),   -- Angina, class II (disorder)
        ('85284003'),   -- Angina, class III (disorder)
        ('89323001'),   -- Angina, class IV (disorder)
        ('15960141000119102'), -- Angina co-occurrent and due to coronary arteriosclerosis
        ('15960061000119102')  -- Unstable angina co-occurrent and due to coronary arteriosclerosis
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
        ('41159611000001100'),  -- Propranolol 10mg tablets 1000 tablet
        ('41159211000001102'),  -- Propranolol 40mg tablets 1000 tablet
        ('8672811000001103'),   -- Propranolol 40mg/5ml oral suspension
        ('8672911000001108'),   -- Propranolol 80mg/5ml oral solution

        -- UK dm+d codes: Atenolol products
        ('42370411000001101'),  -- Atenolol 100mg tablet
        ('42370611000001103'),  -- Atenolol 25mg tablet
        ('42370711000001107'),  -- Atenolol 50mg tablet
        ('282111000001106'),    -- Atenolol 100mg tablets (Sandoz)
        ('884011000001109'),    -- Atenolol 50mg tablets (Sandoz)
        ('393011000001109'),    -- Atenolol 25mg tablets (Sandoz)
        ('12014311000001109'),  -- Atenolol 10mg/5ml oral solution
        ('12015011000001105'),  -- Atenolol 25mg/5ml oral solution

        -- UK dm+d codes: Metoprolol products
        ('39992211000001108'),  -- Metoprolol 25mg tablet
        ('42377311000001109'),  -- Metoprolol 100mg tablet
        ('42377411000001102'),  -- Metoprolol 50mg tablet
        ('519211000001104'),    -- Metoprolol 50mg tablets (Sandoz)
        ('573311000001103'),    -- Metoprolol 100mg tablets (Sandoz)
        ('8668011000001102'),   -- Metoprolol 10mg/5ml oral solution
        ('8668711000001100'),   -- Metoprolol 25mg/5ml oral solution

        -- UK dm+d codes: Bisoprolol products
        ('42371511000001109'),  -- Bisoprolol 5mg tablet
        ('42371211000001106'),  -- Bisoprolol 10mg tablet
        ('42371311000001103'),  -- Bisoprolol 2.5mg tablet
        ('42371411000001105'),  -- Bisoprolol 3.75mg tablet
        ('42371611000001108'),  -- Bisoprolol 7.5mg tablet
        ('42371111000001100'),  -- Bisoprolol 1.25mg tablet
        ('7376711000001106'),   -- Bisoprolol 5mg tablets (Sandoz)
        ('7376911000001108'),   -- Bisoprolol 10mg tablets (Sandoz)
        ('8305111000001102'),   -- Bisoprolol 1mg/5ml oral solution
        ('8304911000001103'),   -- Bisoprolol 5mg/5ml oral solution

        -- UK dm+d codes: Carvedilol products
        ('42372611000001102'),  -- Carvedilol 25mg tablet
        ('42372711000001106'),  -- Carvedilol 3.125mg tablet
        ('42372811000001103'),  -- Carvedilol 6.25mg tablet
        ('42372511000001101'),  -- Carvedilol 12.5mg tablet
        ('7377711000001109'),   -- Carvedilol 25mg tablets (Sandoz)
        ('7377111000001108'),   -- Carvedilol 3.125mg tablets (Sandoz)
        ('7377311000001105'),   -- Carvedilol 6.25mg tablets (Sandoz)
        ('7377511000001104'),   -- Carvedilol 12.5mg tablets (Sandoz)

        -- UK dm+d codes: Sotalol products
        ('42382611000001105'),  -- Sotalol 40mg tablet
        ('42382511000001106'),  -- Sotalol 200mg tablet
        ('42382411000001107'),  -- Sotalol 160mg tablet
        ('42382711000001101'),  -- Sotalol 80mg tablet
        ('646911000001102'),    -- Sotalol 160mg tablets (Sandoz)
        ('170011000001101'),    -- Sotalol 80mg tablets (Sandoz)
        ('8726611000001108'),   -- Sotalol 10mg/5ml oral solution
        ('8727411000001107'),   -- Sotalol 80mg/5ml oral solution

        -- UK dm+d codes: Nebivolol products
        ('39701011000001101'),  -- Nebivolol 10mg tablet
        ('39701211000001106'),  -- Nebivolol 5mg tablet
        ('38659211000001107'),  -- Nebivolol 1.25mg tablet
        ('39701111000001100'),  -- Nebivolol 2.5mg tablet
        ('20312411000001102'),  -- Nebivolol 5mg tablets (Sandoz)

        -- UK dm+d codes: Labetalol products
        ('42375811000001105'),  -- Labetalol 200mg tablet
        ('42375711000001102'),  -- Labetalol 100mg tablet
        ('42375911000001100'),  -- Labetalol 400mg tablet
        ('42376011000001108'),  -- Labetalol 50mg tablet
        ('311711000001109'),    -- Labetalol 100mg tablets (Sandoz)
        ('341511000001108'),    -- Labetalol 200mg tablets (Sandoz)
        ('929111000001109'),    -- Labetalol 400mg tablets (Sandoz)
        ('8582311000001109'),   -- Labetalol 50mg/5ml oral solution

        -- UK dm+d codes: Nadolol products
        ('42377811000001100'),  -- Nadolol 40mg tablet
        ('42378011000001107'),  -- Nadolol 80mg tablet
        ('12300711000001104'),  -- Nadolol 40mg/5ml oral solution
        ('15227111000001100')   -- Nadolol 80mg/5ml oral solution
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

patients_with_chd AS (
    -- Find patients with ANY coronary heart disease diagnosis
    -- These patients will be EXCLUDED from the filter
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        MIN(ge.EventDate) as earliest_chd_date
    FROM {gp_events_enriched} ge
    WHERE ge.SuppliedCode IN (SELECT code FROM chd_codes)
    GROUP BY ge.FK_Patient_Link_ID
),

patients_asthma_no_chd AS (
    -- Find patients with asthma but NO history of CHD
    SELECT
        pa.FK_Patient_Link_ID,
        pa.earliest_asthma_date
    FROM patients_with_asthma pa
    LEFT JOIN patients_with_chd pc
        ON pa.FK_Patient_Link_ID = pc.FK_Patient_Link_ID
    WHERE pc.FK_Patient_Link_ID IS NULL  -- Exclude patients with any CHD history
),

patients_with_beta_blocker AS (
    -- Find patients prescribed beta blockers after their asthma diagnosis
    -- Only include patients without CHD history
    SELECT DISTINCT
        panc.FK_Patient_Link_ID,
        p.medication_start_date as beta_blocker_start_date,
        p.medication_end_date as beta_blocker_end_date,
        p.medication_code as beta_blocker_code,
        p.medication_name as beta_blocker_name
    FROM patients_asthma_no_chd panc
    INNER JOIN {gp_prescriptions} p
        ON panc.FK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE p.medication_code IN (SELECT code FROM beta_blocker_codes)
        AND p.medication_start_date >= panc.earliest_asthma_date
)

-- Return patient IDs matching this filter with period dates
SELECT DISTINCT
    FK_Patient_Link_ID,
    '004' as filter_id,
    beta_blocker_start_date as start_date,
    beta_blocker_end_date as end_date
FROM patients_with_beta_blocker;
