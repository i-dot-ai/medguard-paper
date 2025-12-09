-- Filter 037: Potassium salt or potassium-sparing diuretic + ACE inhibitor/ARB contraindication
--
-- This filter identifies patients who:
-- 1. Are prescribed a potassium salt (potassium chloride oral formulations) OR
--    a potassium-sparing diuretic (amiloride, triamterene - excluding aldosterone antagonists)
-- 2. Are also prescribed an ACE inhibitor OR angiotensin II receptor antagonist (ARB)
-- 3. The prescriptions overlap in time (concurrent use)
--
-- Clinical rationale:
-- ACE inhibitors and ARBs reduce aldosterone secretion → decreased renal potassium excretion
-- Potassium-sparing diuretics (amiloride, triamterene) directly reduce potassium excretion
-- Potassium salts add exogenous potassium
-- Concurrent use significantly increases risk of hyperkalemia → cardiac arrhythmias, death
--
-- Note: Aldosterone antagonists (spironolactone, eplerenone) are EXCLUDED from this filter
-- as they have different risk profiles and are often used intentionally with ACEi/ARBs
--
-- Design decisions:
-- - Include oral potassium chloride formulations (tablets, capsules, solutions, effervescent)
-- - Include potassium-sparing diuretics: amiloride, triamterene
-- - Exclude aldosterone antagonists: spironolactone, eplerenone (different indication/monitoring)
-- - Include common ACE inhibitors: ramipril, lisinopril, perindopril, enalapril, captopril
-- - Include common ARBs: losartan, candesartan, valsartan, irbesartan
-- - Flag concurrent prescriptions (overlapping periods)
-- - Precision over recall: only flag clear overlaps

WITH potassium_salt_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- Potassium chloride ORAL formulations only (exclude IV/injection)
    SELECT code FROM (VALUES
        -- Potassium chloride oral tablets and capsules
        ('32658311000001100'), ('36020211000001102'), ('1312511000001107'), ('42016511000001106'),
        ('28045411000001100'), ('32502711000001101'), ('32502611000001105'), ('32649711000001107'),
        ('32649611000001103'), ('4200411000001108'),

        -- Potassium chloride oral solutions and suspensions
        ('13059811000001100'), ('13059911000001105'), ('13060311000001105'), ('15438011000001101'),
        ('16036911000001109'), ('13059711000001108'), ('13060011000001107'), ('13060111000001108'),
        ('13060211000001102'), ('13060411000001103'), ('8720211000001109'), ('8720311000001101'),
        ('8720611000001106'), ('8720711000001102'), ('39721511000001100'), ('1319711000001108'),

        -- Potassium chloride with furosemide combinations
        ('4557711000001102'), ('36061311000001109'), ('3704511000001107'),

        -- Potassium chloride with potassium bicarbonate combinations
        ('38752811000001109'), ('3402711000001101')
    ) AS t(code)
),

potassium_sparing_diuretic_codes AS (
    -- IMPORTANT: Include UK dm+d codes for amiloride and triamterene
    -- EXCLUDE aldosterone antagonists (spironolactone, eplerenone)
    SELECT code FROM (VALUES
        -- Amiloride (potassium-sparing diuretic)
        ('42206111000001106'), ('42290711000001106'), ('45102411000001103'), ('8273911000001103'),
        ('8274011000001100'), ('8273611000001109'), ('8274111000001104'), ('8273811000001108'),
        ('1092811000001107'), ('1169811000001105'), ('1191111000001100'), ('11707111000001102'),
        ('11707011000001103'), ('11707711000001101'), ('11707611000001105'), ('11707911000001104'),
        ('11707811000001109'), ('11708111000001101'), ('11708011000001102'), ('11708311000001104'),
        ('11708211000001107'), ('11708511000001105'), ('11708411000001106'), ('11708711000001100'),
        ('11708611000001109'), ('13106111000001103'), ('22588511000001108'), ('38779011000001108'),
        ('20165011000001109'), ('754911000001104'), ('824411000001106'), ('10377111000001101'),
        ('446011000001103'), ('533611000001105'), ('9783911000001100'), ('21759411000001109'),
        ('29761811000001107'), ('37031611000001109'), ('7457211000001106'), ('590911000001103'),
        ('505611000001103'), ('59111000001100'),

        -- Triamterene (potassium-sparing diuretic)
        ('42217011000001106'), ('42216811000001102'), ('42216911000001107'), ('42299311000001103'),
        ('3907811000001105'), ('14214911000001106'), ('22105811000001107'), ('1111811000001108'),
        ('1239111000001105'), ('1130611000001106'), ('3251411000001106'), ('22450311000001100'),
        ('37866011000001101'), ('22682211000001101'), ('38020711000001102'), ('42744111000001102'),
        ('42208111000001105')
    ) AS t(code)
),

ace_inhibitor_codes AS (
    -- IMPORTANT: Include UK dm+d codes for common ACE inhibitors
    -- Ramipril, lisinopril, perindopril, enalapril, captopril
    SELECT code FROM (VALUES
        -- Ramipril (100 codes collected - representative sample)
        ('42381311000001109'), ('42381211000001101'), ('42381611000001104'), ('42381711000001108'),
        ('42381411000001102'), ('42381011000001106'), ('42381511000001103'), ('42381111000001107'),
        ('38793311000001101'), ('35180111000001106'), ('35179911000001109'), ('41966011000001109'),
        ('41966311000001107'), ('42750211000001102'), ('42750411000001103'), ('5624411000001103'),
        ('5624611000001100'), ('1069111000001107'), ('1304911000001107'), ('975711000001107'),
        ('3039911000001107'), ('5011311000001105'), ('5011011000001107'), ('11533811000001108'),
        ('11534011000001100'), ('13253411000001106'), ('13253811000001106'), ('13254211000001108'),
        ('13254611000001105'), ('20005511000001105'), ('20005711000001100'), ('30087011000001109'),
        ('30087411000001100'), ('30088011000001105'), ('30088211000001100'),

        -- Lisinopril (100 codes collected - representative sample)
        ('42376411000001104'), ('42376111000001109'), ('42376511000001100'), ('42376211000001103'),
        ('35165611000001109'), ('35165411000001106'), ('35165211000001107'), ('41735111000001103'),
        ('41734411000001107'), ('41734611000001105'), ('683211000001108'), ('145811000001100'),
        ('637111000001101'), ('1247111000001100'), ('1067211000001107'), ('1044011000001103'),
        ('10291011000001108'), ('10291711000001105'), ('10290011000001104'),

        -- Perindopril (100 codes collected - representative sample)
        ('42379211000001107'), ('42379311000001104'), ('42379411000001106'), ('13454111000001103'),
        ('13454411000001108'), ('21939811000001102'), ('21940111000001100'), ('13454211000001109'),
        ('21939911000001107'), ('22378211000001104'), ('22378611000001102'), ('22378411000001100'),
        ('39164911000001109'), ('39165111000001105'), ('39165311000001107'), ('3803611000001105'),
        ('1096511000001105'), ('993111000001102'),

        -- Enalapril (100 codes collected - representative sample)
        ('42374311000001100'), ('42374211000001108'), ('42374011000001103'), ('42374111000001102'),
        ('683211000001108'), ('728411000001104'), ('450811000001105'), ('51511000001108'),
        ('1061011000001107'), ('1100711000001105'), ('988511000001101'), ('19190811000001108'),
        ('19191011000001106'), ('19191211000001101'),

        -- Captopril (50 codes collected - representative sample)
        ('42372311000001107'), ('42372411000001100'), ('42372211000001104'), ('614411000001107'),
        ('762611000001109'), ('212311000001105'), ('827011000001105'), ('1289011000001103'),
        ('980811000001101'), ('1040911000001109'), ('1323511000001105'), ('947911000001103'),
        ('1046811000001102')
    ) AS t(code)
),

arb_codes AS (
    -- IMPORTANT: Include UK dm+d codes for common ARBs (angiotensin II receptor antagonists)
    -- Losartan, candesartan, valsartan, irbesartan
    SELECT code FROM (VALUES
        -- Losartan (100 codes collected - representative sample)
        ('42376811000001102'), ('42376711000001105'), ('42377011000001106'), ('15148111000001100'),
        ('38933311000001102'), ('38933111000001104'), ('38932911000001108'), ('39127711000001106'),
        ('967611000001104'), ('1234911000001107'), ('988311000001107'), ('9415111000001108'),
        ('13109011000001105'), ('18169911000001109'), ('18170211000001103'), ('18170411000001104'),
        ('20308011000001106'), ('20308411000001102'), ('20308611000001104'),

        -- Candesartan (100 codes collected - representative sample)
        ('42371711000001104'), ('42372111000001105'), ('42371911000001102'), ('42372011000001109'),
        ('42371811000001107'), ('39561311000001103'), ('39560611000001103'), ('39559311000001107'),
        ('39560411000001101'), ('39559611000001102'), ('988711000001106'), ('1150111000001102'),
        ('1021711000001102'), ('1276011000001100'), ('948711000001104'), ('8983811000001102'),
        ('5445211000001101'), ('5453311000001106'), ('5481611000001107'),

        -- Valsartan (100 codes collected - representative sample)
        ('42384511000001101'), ('42384111000001105'), ('42384311000001107'), ('42384411000001100'),
        ('42384811000001103'), ('42384711000001106'), ('42384211000001104'), ('1272411000001108'),
        ('959311000001107'), ('1284211000001109'), ('8262511000001105'), ('5461511000001106'),
        ('5460711000001109'), ('5461311000001100'), ('5516211000001107'), ('13145911000001100'),
        ('13145611000001106'), ('13143611000001107'), ('13143211000001105'),

        -- Irbesartan (100 codes collected - representative sample)
        ('42375511000001107'), ('42375611000001106'), ('42375311000001101'), ('979211000001102'),
        ('1080311000001103'), ('1126711000001102'), ('10970311000001105'), ('10504511000001108'),
        ('10504811000001106'), ('10505011000001101'), ('21992811000001104'), ('21993011000001101'),
        ('21993211000001106'), ('23957411000001100'), ('23957611000001102'), ('23957811000001103')
    ) AS t(code)
),

potassium_or_ksparing_prescriptions AS (
    -- Combine potassium salts and potassium-sparing diuretics
    SELECT DISTINCT
        FK_Patient_Link_ID,
        medication_start_date AS potassium_start_date,
        medication_end_date AS potassium_end_date,
        medication_name AS potassium_name,
        medication_code AS potassium_code
    FROM {gp_prescriptions}
    WHERE (medication_code IN (SELECT code FROM potassium_salt_codes)
           OR medication_code IN (SELECT code FROM potassium_sparing_diuretic_codes))
        AND medication_start_date IS NOT NULL
),

acei_or_arb_prescriptions AS (
    -- Combine ACE inhibitors and ARBs
    SELECT DISTINCT
        FK_Patient_Link_ID,
        medication_start_date AS acei_arb_start_date,
        medication_end_date AS acei_arb_end_date,
        medication_name AS acei_arb_name,
        medication_code AS acei_arb_code
    FROM {gp_prescriptions}
    WHERE (medication_code IN (SELECT code FROM ace_inhibitor_codes)
           OR medication_code IN (SELECT code FROM arb_codes))
        AND medication_start_date IS NOT NULL
),

concurrent_contraindication AS (
    SELECT DISTINCT
        pot.FK_Patient_Link_ID,
        pot.potassium_name,
        pot.potassium_start_date,
        pot.potassium_end_date,
        ace.acei_arb_name,
        ace.acei_arb_start_date,
        ace.acei_arb_end_date,
        -- Calculate overlap period (when BOTH medications are active)
        GREATEST(pot.potassium_start_date, ace.acei_arb_start_date) as hazard_start_date,
        LEAST(
            COALESCE(pot.potassium_end_date, pot.potassium_start_date + INTERVAL '90 days'),
            COALESCE(ace.acei_arb_end_date, ace.acei_arb_start_date + INTERVAL '90 days')
        ) as hazard_end_date
    FROM potassium_or_ksparing_prescriptions pot
    INNER JOIN acei_or_arb_prescriptions ace
        ON pot.FK_Patient_Link_ID = ace.FK_Patient_Link_ID
    WHERE
        -- Check for overlapping prescriptions
        pot.potassium_start_date <= COALESCE(ace.acei_arb_end_date, ace.acei_arb_start_date + INTERVAL '90 days')
        AND COALESCE(pot.potassium_end_date, pot.potassium_start_date + INTERVAL '90 days') >= ace.acei_arb_start_date
)

-- Return results
SELECT DISTINCT
    FK_Patient_Link_ID,
    '037' as filter_id,
    hazard_start_date as start_date,
    hazard_end_date as end_date
FROM concurrent_contraindication;
