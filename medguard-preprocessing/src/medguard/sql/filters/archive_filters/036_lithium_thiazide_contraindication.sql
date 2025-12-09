-- Filter 036: Lithium + thiazide diuretic contraindication
--
-- This filter identifies patients who:
-- 1. Are prescribed lithium (carbonate or citrate formulations)
-- 2. Are also prescribed a thiazide or thiazide-like diuretic
-- 3. The prescriptions overlap in time (concurrent use)
--
-- Clinical rationale:
-- Thiazide diuretics can increase lithium levels by reducing renal lithium clearance
-- - Thiazides reduce sodium reabsorption in the distal tubule
-- - Compensatory proximal tubule sodium/lithium reabsorption increases
-- - This leads to reduced lithium clearance and increased serum lithium levels
-- - Risk of lithium toxicity (tremor, confusion, seizures, renal damage)
-- - Well-established drug interaction requiring close monitoring or alternative diuretic
--
-- Design decisions:
-- - Include ALL lithium formulations (carbonate, citrate, modified-release, oral solution)
-- - Include thiazides: bendroflumethiazide, hydrochlorothiazide
-- - Include thiazide-like diuretics: indapamide, chlortalidone, metolazone, xipamide
-- - Flag concurrent prescriptions (overlapping periods)
-- - Hazardous period = overlap between lithium and thiazide/thiazide-like diuretic
-- - Precision over recall: only flag clear overlaps

WITH lithium_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- These codes match actual UK prescription data
    -- Reused from filter 051
    SELECT code FROM (VALUES
        -- Lithium carbonate tablets
        ('963211000001105'), ('30760011000001108'), ('30760111000001109'), ('30802011000001105'),
        ('30802211000001100'), ('30988111000001104'), ('42295711000001101'),

        -- Lithium carbonate modified-release tablets
        ('1114411000001108'), ('1269111000001100'), ('1306011000001103'), ('36040211000001104'),
        ('39110011000001104'), ('39110111000001103'), ('4818611000001104'),

        -- Lithium carbonate oral suspension
        ('8658611000001103'), ('8628811000001100'), ('8628711000001108'), ('8628911000001105'),

        -- Lithium citrate modified-release tablets
        ('4559411000001104'), ('4543211000001102'),

        -- Lithium citrate oral solution
        ('3832111000001104'), ('36040311000001107'), ('4888511000001101'), ('8788611000001101'),
        ('42295811000001109'), ('42295911000001104'),

        -- Brand names
        ('9311401000001108'), ('9311501000001107')
    ) AS t(code)
),

thiazide_codes AS (
    -- IMPORTANT: Include UK dm+d codes for all thiazide and thiazide-like diuretics
    -- Includes: bendroflumethiazide, hydrochlorothiazide, indapamide,
    --           chlortalidone, metolazone, xipamide
    SELECT code FROM (VALUES
        -- Bendroflumethiazide (thiazide)
        ('42206711000001107'), ('42206611000001103'), ('40673811000001109'), ('42377711000001108'),
        ('42377911000001105'), ('8306911000001106'), ('8306711000001109'), ('1007111000001100'),
        ('1295211000001106'), ('1039611000001105'), ('1226811000001107'), ('12226311000001103'),
        ('12226411000001105'), ('13181711000001107'), ('22617011000001105'), ('38805211000001108'),
        ('40673611000001105'), ('720911000001105'), ('42380411000001106'), ('42383311000001105'),
        ('42370511000001102'), ('42391911000001109'), ('12285211000001105'), ('8306811000001101'),
        ('12285311000001102'), ('8307011000001105'), ('143511000001102'), ('7487011000001109'),
        ('1180311000001107'), ('1119411000001107'), ('10384111000001103'), ('159711000001108'),
        ('436711000001100'), ('9793111000001104'), ('13181411000001101'), ('15986811000001102'),
        ('17196011000001105'), ('21782811000001109'), ('22616411000001103'), ('29774211000001101'),
        ('32661411000001109'), ('34015811000001107'), ('38805011000001103'), ('532811000001101'),
        ('169811000001105'), ('1711000001109'), ('288611000001101'), ('320511000001104'),
        ('8286211000001106'), ('8287311000001100'),

        -- Hydrochlorothiazide (thiazide)
        ('42211711000001104'), ('42211611000001108'), ('24594211000001108'), ('40536611000001109'),
        ('40536411000001106'), ('42384011000001109'), ('42376611000001101'), ('8529011000001108'),
        ('8529411000001104'), ('8529111000001109'), ('8529511000001100'), ('8529611000001101'),
        ('8529711000001105'), ('4546111000001103'), ('4543711000001109'), ('10970311000001105'),
        ('12506311000001103'), ('12506411000001105'), ('12506511000001109'), ('12506611000001108'),
        ('12538511000001102'), ('12538611000001103'), ('12538711000001107'), ('12538811000001104'),
        ('12539311000001102'), ('12539411000001109'), ('12539511000001108'), ('12539611000001107'),
        ('13731911000001109'), ('20529211000001103'), ('20529111000001109'), ('20528811000001109'),
        ('39691911000001109'), ('39725011000001105'), ('39733811000001100'), ('39693411000001102'),
        ('42213111000001104'), ('42375411000001108'), ('42376311000001106'), ('42384611000001102'),
        ('42377211000001101'), ('42375211000001109'), ('42383911000001106'), ('42382911000001104'),
        ('42383111000001108'), ('42376911000001107'), ('18036711000001103'), ('8529211000001103'),
        ('8529311000001106'), ('10270711000001105'), ('12538911000001109'), ('12539011000001100'),
        ('12539111000001104'), ('12539211000001105'), ('13112711000001103'),

        -- Indapamide (thiazide-like)
        ('22209311000001103'), ('22209411000001105'), ('22209511000001109'), ('39696211000001108'),
        ('39020711000001100'), ('21578911000001105'), ('692411000001104'), ('1320111000001108'),
        ('1305511000001104'), ('1170911000001102'), ('1171411000001101'), ('13579511000001104'),
        ('35593111000001109'), ('38997911000001104'), ('41972311000001103'), ('39949711000001102'),
        ('397311000001100'), ('598411000001109'), ('8139411000001107'), ('10380011000001106'),
        ('10437611000001100'), ('711711000001108'), ('13454311000001101'), ('3437611000001100'),
        ('14784911000001103'), ('21940011000001101'), ('21924511000001102'), ('29877611000001107'),
        ('55911000001104'), ('37422411000001108'), ('38348411000001105'), ('214811000001107'),
        ('146711000001100'), ('450511000001107'), ('14598711000001105'), ('1144411000001103'),

        -- Chlortalidone (thiazide-like)
        ('42207211000001103'), ('42207311000001106'), ('39565011000001104'), ('38124811000001109'),
        ('42216911000001107'), ('8359911000001106'), ('1079211000001106'), ('23667511000001105'),
        ('26589211000001101'), ('37705111000001107'), ('38831911000001108'), ('39534011000001109'),
        ('23667611000001109'), ('26589411000001102'), ('31989011000001101'), ('38124911000001104'),
        ('8342111000001101'), ('8341911000001109'), ('3251411000001106'),

        -- Metolazone (thiazide-like)
        ('42213711000001103'), ('42213611000001107'), ('40531711000001106'), ('40559211000001102'),
        ('24502311000001105'), ('1245311000001106'), ('13005711000001100'), ('13005811000001108'),
        ('13006111000001107'), ('13006211000001101'), ('13006311000001109'), ('13006411000001102'),
        ('21574511000001105'), ('24502211000001102'), ('40531211000001104'), ('24502011000001107'),
        ('13006011000001106'), ('13005911000001103'), ('13005611000001109'), ('13005511000001105'),
        ('21574811000001108'), ('24501911000001100'),

        -- Xipamide (thiazide-like)
        ('42218011000001107'), ('1207611000001104')
    ) AS t(code)
),

lithium_prescriptions AS (
    SELECT DISTINCT
        FK_Patient_Link_ID,
        medication_start_date AS lithium_start_date,
        medication_end_date AS lithium_end_date,
        medication_name AS lithium_name,
        medication_code AS lithium_code
    FROM {gp_prescriptions}
    WHERE medication_code IN (SELECT code FROM lithium_codes)
        AND medication_start_date IS NOT NULL
),

thiazide_prescriptions AS (
    SELECT DISTINCT
        FK_Patient_Link_ID,
        medication_start_date AS thiazide_start_date,
        medication_end_date AS thiazide_end_date,
        medication_name AS thiazide_name,
        medication_code AS thiazide_code
    FROM {gp_prescriptions}
    WHERE medication_code IN (SELECT code FROM thiazide_codes)
        AND medication_start_date IS NOT NULL
),

concurrent_contraindication AS (
    SELECT DISTINCT
        li.FK_Patient_Link_ID,
        li.lithium_name,
        li.lithium_start_date,
        li.lithium_end_date,
        th.thiazide_name,
        th.thiazide_start_date,
        th.thiazide_end_date,
        -- Calculate overlap period (when BOTH medications are active)
        GREATEST(li.lithium_start_date, th.thiazide_start_date) as hazard_start_date,
        LEAST(
            COALESCE(li.lithium_end_date, li.lithium_start_date + INTERVAL '90 days'),
            COALESCE(th.thiazide_end_date, th.thiazide_start_date + INTERVAL '90 days')
        ) as hazard_end_date
    FROM lithium_prescriptions li
    INNER JOIN thiazide_prescriptions th
        ON li.FK_Patient_Link_ID = th.FK_Patient_Link_ID
    WHERE
        -- Check for overlapping prescriptions
        li.lithium_start_date <= COALESCE(th.thiazide_end_date, th.thiazide_start_date + INTERVAL '90 days')
        AND COALESCE(li.lithium_end_date, li.lithium_start_date + INTERVAL '90 days') >= th.thiazide_start_date
)

-- Return results
SELECT DISTINCT
    FK_Patient_Link_ID,
    '036' as filter_id,
    hazard_start_date as start_date,
    hazard_end_date as end_date
FROM concurrent_contraindication;
