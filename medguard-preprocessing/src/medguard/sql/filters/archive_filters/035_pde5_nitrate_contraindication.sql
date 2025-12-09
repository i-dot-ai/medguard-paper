-- Filter 035: PDE5 inhibitor + nitrate/nicorandil contraindication
--
-- This filter identifies patients who:
-- 1. Are prescribed a phosphodiesterase type-5 (PDE5) inhibitor (sildenafil, tadalafil, vardenafil, avanafil)
-- 2. Are also prescribed a nitrate (GTN, isosorbide mononitrate, isosorbide dinitrate) or nicorandil
-- 3. The prescriptions overlap in time (concurrent use)
--
-- Clinical rationale:
-- PDE5 inhibitors are absolutely contraindicated with nitrates/nicorandil because:
-- - Both cause vasodilation via different mechanisms
-- - Concurrent use can cause severe, life-threatening hypotension
-- - This applies to all nitrate formulations (oral, sublingual, transdermal, spray)
-- - Nicorandil has nitrate-like effects and carries the same risk
--
-- Design decisions:
-- - Include ALL PDE5 inhibitors (sildenafil, tadalafil, vardenafil, avanafil)
-- - Include ALL nitrate formulations (GTN tablets/spray/patches, isosorbide mono/dinitrate)
-- - Include nicorandil (has nitrate-like vasodilator properties)
-- - Flag concurrent prescriptions (overlapping periods)
-- - Hazardous period = overlap between PDE5 inhibitor and nitrate/nicorandil
-- - Precision over recall: only flag clear overlaps

WITH pde5_inhibitor_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- These codes match actual UK prescription data
    SELECT code FROM (VALUES
        -- Sildenafil (various strengths and formulations)
        ('42089311000001109'), ('42089411000001102'), ('42089611000001104'), ('42089511000001103'),
        ('22099011000001107'), ('15650211000001105'), ('13859611000001103'), ('35839511000001108'),
        ('15452511000001106'), ('14058011000001104'), ('14160211000001106'), ('13859711000001107'),
        ('14058111000001103'), ('15452411000001107'), ('15650111000001104'), ('14160311000001103'),
        ('15535611000001107'), ('15535711000001103'), ('21705011000001109'), ('42677811000001107'),
        ('39361511000001107'), ('39179311000001103'), ('41618211000001103'), ('41618511000001100'),
        ('40698111000001101'), ('40698711000001100'), ('40699111000001108'), ('40699611000001100'),
        ('41233211000001102'), ('41232711000001101'), ('41233011000001107'), ('41249111000001107'),
        ('949111000001107'), ('1118711000001105'), ('1088011000001104'), ('1011811000001102'),
        ('1039111000001102'), ('1127111000001100'), ('10154411000001105'), ('22089311000001106'),
        ('22089211000001103'), ('24513711000001104'), ('24514511000001107'), ('24516111000001105'),
        ('24640311000001106'), ('30096211000001102'), ('30096511000001104'), ('30096811000001101'),
        ('33972911000001107'), ('33973511000001107'), ('33974111000001101'), ('35184611000001105'),
        ('35184911000001104'), ('44948011000001109'), ('44948111000001105'), ('22648811000001107'),
        ('22649011000001106'), ('22648911000001102'), ('44947911000001107'), ('18759411000001103'),
        ('16660911000001106'), ('44547011000001102'),

        -- Tadalafil (various strengths)
        ('42090211000001107'), ('42090011000001102'), ('42090111000001101'), ('15098011000001101'),
        ('37906211000001104'), ('37818111000001102'), ('37818511000001106'), ('37818311000001100'),
        ('37979211000001102'), ('37979011000001107'), ('37906711000001106'), ('41522711000001107'),
        ('42300111000001102'), ('37905211000001105'), ('44113211000001104'), ('44965911000001105'),
        ('44966311000001104'), ('44966111000001101'), ('4106211000001108'), ('4106111000001102'),
        ('4105811000001101'), ('15001611000001102'), ('18248911000001108'), ('34960611000001108'),
        ('34960811000001107'), ('34961011000001105'), ('35185811000001105'), ('35186011000001108'),
        ('45323411000001106'),

        -- Vardenafil (various strengths)
        ('39706811000001102'), ('39706511000001100'), ('39706711000001105'), ('37833111000001101'),
        ('37833511000001105'), ('37833311000001104'), ('4362611000001104'), ('4362211000001101'),
        ('4361511000001106'), ('4361411000001107'), ('4361011000001103'), ('4360911000001106'),
        ('18684711000001105'), ('39923111000001104'), ('39923611000001107'), ('39922411000001100'),
        ('40847011000001101'), ('40846511000001107'), ('36235211000001101'), ('36235511000001103'),
        ('36235811000001100'),

        -- Avanafil (various strengths)
        ('42080611000001105'), ('42080711000001101'), ('42080511000001106'), ('24397011000001109'),
        ('24396911000001105'), ('24396511000001103'), ('24396411000001102'), ('24395811000001108'),
        ('24395711000001100')
    ) AS t(code)
),

nitrate_codes AS (
    -- IMPORTANT: Include UK dm+d codes for all nitrate formulations
    -- Includes: GTN (tablets, sublingual, spray, patches, ointment),
    --           isosorbide mononitrate, isosorbide dinitrate
    SELECT code FROM (VALUES
        -- Glyceryl trinitrate (GTN) - all formulations
        ('16109611000001108'), ('41899011000001105'), ('42211211000001106'), ('42211111000001100'),
        ('42211011000001101'), ('41899111000001106'), ('9055911000001106'), ('9056111000001102'),
        ('15648511000001108'), ('15774611000001105'), ('36774711000001102'), ('39024811000001103'),
        ('9315411000001108'), ('16103111000001103'), ('16103011000001104'), ('36051611000001109'),
        ('36051811000001108'), ('36051911000001103'), ('2843711000001100'), ('1127511000001109'),
        ('1041911000001102'), ('1238011000001104'), ('18357911000001103'), ('18358011000001101'),
        ('35009011000001106'), ('35008811000001107'), ('36052011000001105'), ('36052711000001107'),
        ('4557911000001100'), ('971611000001101'), ('1197711000001108'), ('1057411000001104'),
        ('1184211000001107'), ('1129011000001105'), ('1046411000001104'), ('3202911000001103'),
        ('3202811000001108'), ('1149611000001101'), ('18247711000001105'), ('18249311000001101'),
        ('35894511000001101'), ('36051711000001100'), ('36052111000001106'), ('36052411000001101'),
        ('36052611000001103'), ('18350811000001109'), ('18350711000001101'), ('18349711000001105'),
        ('18349611000001101'),

        -- Isosorbide mononitrate (all strengths and formulations)
        ('39832211000001109'), ('42212611000001102'), ('42212511000001101'), ('42212411000001100'),
        ('38898211000001103'), ('38898311000001106'), ('39022111000001102'), ('39024411000001100'),
        ('39024211000001104'), ('39024111000001105'), ('39022011000001103'), ('39024311000001107'),
        ('1303811000001100'), ('1203111000001104'), ('1007211000001106'), ('1276211000001105'),
        ('1258611000001105'), ('1071511000001108'), ('955511000001104'), ('1166211000001100'),
        ('1025211000001107'), ('1044711000001101'), ('1051111000001102'), ('1275711000001106'),
        ('8563011000001100'), ('8579911000001106'), ('8580011000001107'), ('8563111000001104'),
        ('8580111000001108'), ('8580211000001102'), ('12643111000001105'), ('12643211000001104'),
        ('12643311000001107'),

        -- Isosorbide dinitrate (all strengths and formulations)
        ('42212211000001104'), ('42212311000001107'), ('42212011000001109'), ('42212111000001105'),
        ('39022211000001108'), ('4556311000001104'), ('8579711000001109'), ('8579811000001101'),
        ('8562811000001103'), ('8562911000001108'), ('4544411000001100'), ('4544311000001107'),
        ('4544211000001104'), ('4543811000001101'), ('1307511000001108'), ('1187911000001109'),
        ('1232311000001104'), ('3285411000001102'), ('12642511000001108'), ('12642611000001107'),
        ('12642711000001103'), ('12642811000001106'), ('12642911000001101'), ('12643011000001109'),
        ('36050311000001109'), ('36050411000001102'), ('36050511000001103'), ('4541611000001104'),
        ('4541511000001103'), ('4540411000001106'), ('4540311000001104'), ('1228511000001105'),
        ('1059711000001102'), ('3056411000001105'), ('3056311000001103'), ('4548211000001105'),
        ('7808511000001107'), ('28928211000001100'), ('28929311000001102'), ('36050111000001107'),
        ('36050211000001101'), ('36050611000001104'), ('42211911000001102')
    ) AS t(code)
),

nicorandil_codes AS (
    -- IMPORTANT: Include UK dm+d codes for nicorandil
    -- Nicorandil has nitrate-like vasodilator effects
    SELECT code FROM (VALUES
        ('42214911000001104'), ('42214811000001109'), ('1319211000001101'), ('1263911000001100'),
        ('14015511000001106'), ('19715711000001102'), ('19715911000001100'), ('30064011000001104'),
        ('30064211000001109'), ('32878611000001103'), ('39052811000001105'), ('39168611000001108'),
        ('19298411000001107'), ('19298711000001101'), ('18730711000001103'), ('18732311000001103'),
        ('19178211000001103'), ('19178411000001104'), ('19606211000001107'), ('19606411000001106'),
        ('19215111000001106'), ('19215511000001102'), ('22387211000001108'), ('22387411000001107'),
        ('18439811000001107'), ('18440011000001108'), ('28732111000001104'), ('28732711000001103'),
        ('20915911000001106'), ('20916111000001102'), ('32425511000001104'), ('32425711000001109'),
        ('13980711000001101'), ('13980611000001105'), ('18541811000001100'), ('18542011000001103'),
        ('18628011000001105'), ('18628311000001108'), ('32846011000001107'), ('32845911000001104'),
        ('18642811000001103'), ('18643011000001100')
    ) AS t(code)
),

pde5_prescriptions AS (
    SELECT DISTINCT
        FK_Patient_Link_ID,
        medication_start_date AS pde5_start_date,
        medication_end_date AS pde5_end_date,
        medication_name AS pde5_name,
        medication_code AS pde5_code
    FROM {gp_prescriptions}
    WHERE medication_code IN (SELECT code FROM pde5_inhibitor_codes)
        AND medication_start_date IS NOT NULL
),

nitrate_prescriptions AS (
    SELECT DISTINCT
        FK_Patient_Link_ID,
        medication_start_date AS nitrate_start_date,
        medication_end_date AS nitrate_end_date,
        medication_name AS nitrate_name,
        medication_code AS nitrate_code
    FROM {gp_prescriptions}
    WHERE medication_code IN (SELECT code FROM nitrate_codes)
        AND medication_start_date IS NOT NULL
),

nicorandil_prescriptions AS (
    SELECT DISTINCT
        FK_Patient_Link_ID,
        medication_start_date AS nicorandil_start_date,
        medication_end_date AS nicorandil_end_date,
        medication_name AS nicorandil_name,
        medication_code AS nicorandil_code
    FROM {gp_prescriptions}
    WHERE medication_code IN (SELECT code FROM nicorandil_codes)
        AND medication_start_date IS NOT NULL
),

-- Combine nitrates and nicorandil into single list
nitrate_or_nicorandil_prescriptions AS (
    SELECT
        FK_Patient_Link_ID,
        nitrate_start_date AS contraindicated_start_date,
        nitrate_end_date AS contraindicated_end_date,
        nitrate_name AS contraindicated_name,
        nitrate_code AS contraindicated_code
    FROM nitrate_prescriptions

    UNION ALL

    SELECT
        FK_Patient_Link_ID,
        nicorandil_start_date AS contraindicated_start_date,
        nicorandil_end_date AS contraindicated_end_date,
        nicorandil_name AS contraindicated_name,
        nicorandil_code AS contraindicated_code
    FROM nicorandil_prescriptions
),

concurrent_contraindication AS (
    SELECT DISTINCT
        pde5.FK_Patient_Link_ID,
        pde5.pde5_name,
        pde5.pde5_start_date,
        pde5.pde5_end_date,
        contra.contraindicated_name,
        contra.contraindicated_start_date,
        contra.contraindicated_end_date,
        -- Calculate overlap period (when BOTH medications are active)
        GREATEST(pde5.pde5_start_date, contra.contraindicated_start_date) as hazard_start_date,
        LEAST(
            COALESCE(pde5.pde5_end_date, pde5.pde5_start_date + INTERVAL '90 days'),
            COALESCE(contra.contraindicated_end_date, contra.contraindicated_start_date + INTERVAL '90 days')
        ) as hazard_end_date
    FROM pde5_prescriptions pde5
    INNER JOIN nitrate_or_nicorandil_prescriptions contra
        ON pde5.FK_Patient_Link_ID = contra.FK_Patient_Link_ID
    WHERE
        -- Check for overlapping prescriptions
        pde5.pde5_start_date <= COALESCE(contra.contraindicated_end_date, contra.contraindicated_start_date + INTERVAL '90 days')
        AND COALESCE(pde5.pde5_end_date, pde5.pde5_start_date + INTERVAL '90 days') >= contra.contraindicated_start_date
)

-- Return results
SELECT DISTINCT
    FK_Patient_Link_ID,
    '035' as filter_id,
    hazard_start_date as start_date,
    hazard_end_date as end_date
FROM concurrent_contraindication;
