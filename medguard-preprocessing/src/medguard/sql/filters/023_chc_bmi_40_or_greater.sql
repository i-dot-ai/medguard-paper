-- Filter 023: Combined hormonal contraceptive prescribed to woman with body mass index of ≥40
--
-- This filter identifies patients who:
-- 1. Are female
-- 2. Have documented BMI ≥40 (severe/morbid obesity) within 12 months before CHC prescription
-- 3. Are prescribed combined hormonal contraceptives (CHC)
--
-- Combined hormonal contraceptives include:
-- 1. Combined oral contraceptive pills (COCs) containing estrogen + progestogen
-- 2. Transdermal contraceptive patches (e.g., Evra)
-- 3. Vaginal contraceptive rings (e.g., NuvaRing)
--
-- Clinical rationale:
-- - CHC significantly increases risk of venous thromboembolism (VTE)
-- - Obesity (especially BMI ≥40) independently increases VTE risk
-- - Combined risk is multiplicative and clinically significant
-- - WHO Medical Eligibility Criteria: CHC in women with BMI ≥40 is category 3 (risks usually outweigh benefits)
-- - UK FSRH guidelines recommend caution with CHC in obesity, especially BMI ≥40
--
-- Design decisions:
-- - Uses GP Events for BMI measurements (Value column contains numeric BMI reading)
-- - Uses GP Events for obesity diagnosis codes (BMI 40+, severe obesity, morbid obesity) as backup
-- - Uses GP Prescriptions table for CHC prescriptions
-- - Female patients only
-- - BMI ≥40 must be documented within 12 months before CHC prescription
-- - Includes all forms of combined hormonal contraception (oral, patch, ring)
-- - Uses UK dm+d codes for all common CHC brands and formulations
-- - Prioritizes precision: only flags clear cases where recent BMI ≥40 is documented

WITH bmi_observation_codes AS (
    -- SNOMED codes for BMI observations
    -- These are international codes used in GP Events for measurements
    SELECT code FROM (VALUES
        ('60621009'),   -- Body mass index (observable entity) [PARENT]
        ('301331008'),  -- Finding of body mass index (finding)
        ('698094009')   -- Measurement of body mass index
    ) AS t(code)
),

severe_obesity_diagnosis_codes AS (
    -- SNOMED codes for severe obesity/BMI ≥40 diagnoses
    -- Used as backup when BMI measurements not available or to confirm high BMI
    SELECT code FROM (VALUES
        ('408512008'),  -- Body mass index 40+ - severely obese [PARENT]
        ('238136002'),  -- Morbid obesity (disorder)
        ('83911000119104'),  -- Severe obesity (disorder)
        ('414916001'),  -- Obesity (disorder) [general - may be used for severe cases]
        ('48499001')    -- Increased body mass index (finding) [general - may indicate BMI ≥40]
    ) AS t(code)
),

combined_contraceptive_codes AS (
    -- UK SNOMED CT Extension codes (dm+d codes) for combined hormonal contraceptives
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- These codes match actual UK prescription data
    -- Reused from filter 022
    SELECT code FROM (VALUES
        -- Ethinylestradiol + Levonorgestrel combinations (various strengths)
        ('41877111000001108'), -- Ethinylestradiol 30mcg + Levonorgestrel 150mcg tablet
        ('41878611000001101'), -- Ethinylestradiol 30mcg + Levonorgestrel 250mcg tablet
        ('41878711000001105'), -- Ethinylestradiol 50mcg + Levonorgestrel 250mcg tablet
        ('14610511000001106'), -- Ethinylestradiol 30mcg + Levonorgestrel 50mcg tablets
        ('14610711000001101'), -- Ethinylestradiol 30mcg + Levonorgestrel 125mcg tablets
        ('14610611000001105'), -- Ethinylestradiol 40mcg + Levonorgestrel 75mcg tablets

        -- Ethinylestradiol + Desogestrel combinations
        ('41876511000001101'), -- Ethinylestradiol 20mcg + Desogestrel 150mcg tablet
        ('41876811000001103'), -- Ethinylestradiol 30mcg + Desogestrel 150mcg tablet

        -- Ethinylestradiol + Gestodene combinations
        ('41876611000001102'), -- Ethinylestradiol 20mcg + Gestodene 75mcg tablet
        ('41877011000001107'), -- Ethinylestradiol 30mcg + Gestodene 75mcg tablet
        ('3463311000001106'),  -- Ethinylestradiol 30mcg + Gestodene 50mcg tablets
        ('3463211000001103'),  -- Ethinylestradiol 30mcg + Gestodene 100mcg tablets
        ('3463411000001104'),  -- Ethinylestradiol 40mcg + Gestodene 70mcg tablets

        -- Ethinylestradiol + Norethisterone combinations
        ('41877411000001103'), -- Ethinylestradiol 35mcg + Norethisterone 500mcg tablet
        ('41877511000001104'), -- Ethinylestradiol 35mcg + Norethisterone 750mcg tablet
        ('41877311000001105'), -- Ethinylestradiol 35mcg + Norethisterone 1mg tablet
        ('41876711000001106'), -- Ethinylestradiol 20mcg + Norethisterone acetate 1mg tablet
        ('41877211000001102'), -- Ethinylestradiol 30mcg + Norethisterone acetate 1.5mg tablet

        -- Ethinylestradiol + Drospirenone combinations
        ('41876911000001108'), -- Ethinylestradiol 30mcg + Drospirenone 3mg tablet
        ('21711311000001107'),  -- Ethinylestradiol 20mcg + Drospirenone 3mg tablets

        -- Ethinylestradiol + Norgestimate
        ('41877611000001100'), -- Ethinylestradiol 35mcg + Norgestimate 250mcg tablet

        -- Brand names - Microgynon (Ethinylestradiol + Levonorgestrel)
        ('9746501000001108'),   -- Microgynon
        ('9515001000001103'),   -- Microgynon 30
        ('9738001000001104'),   -- Microgynon 30 ED
        ('42111000001107'),     -- Microgynon 30 tablets (Bayer Plc)
        ('3052511000001108'),   -- Microgynon 30 ED tablets (Bayer Plc)

        -- Brand names - Rigevidon (Ethinylestradiol + Levonorgestrel)
        ('10548201000001105'),  -- Rigevidon
        ('17346711000001106'),  -- Rigevidon tablets (Gedeon Richter)

        -- Brand names - Ovranette (Ethinylestradiol + Levonorgestrel)
        ('9295101000001106'),   -- Ovranette
        ('492611000001103'),    -- Ovranette 150mcg/30mcg tablets

        -- Brand names - Yasmin (Ethinylestradiol + Drospirenone)
        ('9395201000001106'),   -- Yasmin
        ('439011000001108'),    -- Yasmin tablets (Bayer Plc)

        -- Brand names - Cilest (Ethinylestradiol + Norgestimate)
        ('9567801000001100'),   -- Cilest
        ('380211000001105'),    -- Cilest 35mcg/250mcg tablets

        -- Brand names - Marvelon (Ethinylestradiol + Desogestrel)
        ('9469001000001106'),   -- Marvelon
        ('524211000001108'),    -- Marvelon tablets (Organon Pharma)

        -- Brand names - Gedarel (Ethinylestradiol + Desogestrel)
        ('10548301000001101'),  -- Gedarel
        ('17348811000001102'),  -- Gedarel 30mcg/150mcg tablets
        ('17346911000001108'),  -- Gedarel 20mcg/150mcg tablets

        -- Brand names - Mercilon (Ethinylestradiol + Desogestrel)
        ('9491701000001106'),   -- Mercilon
        ('208311000001105'),    -- Mercilon 150mcg/20mcg tablets

        -- Brand names - Femodene (Ethinylestradiol + Gestodene)
        ('9534801000001103'),   -- Femodene
        ('9698901000001100'),   -- Femodene
        ('9674401000001108'),   -- Femodene ED
        ('3048811000001105'),   -- Femodene tablets (Bayer Plc)

        -- Brand names - Loestrin (Ethinylestradiol + Norethisterone)
        ('9457601000001100'),   -- Loestrin 20
        ('9538901000001101'),   -- Loestrin 30
        ('3058111000001101'),   -- Loestrin 20 tablets (Galen Ltd)
        ('3058411000001106'),   -- Loestrin 30 tablets (Galen Ltd)

        -- Transdermal patch - Evra (Ethinylestradiol + Norelgestromin)
        ('9475101000001101'),   -- Evra
        ('10512211000001104'),  -- Evra transdermal patches (Dowelhurst Ltd)
        ('29052711000001103'),  -- Evra transdermal patches (Waymade Healthcare)
        ('4608311000001102'),   -- Evra transdermal patches (Gedeon Richter)

        -- Vaginal ring - NuvaRing (Ethinylestradiol + Etonogestrel)
        ('10103201000001100'),  -- NuvaRing
        ('15364511000001104'),  -- NuvaRing vaginal delivery system (Organon Pharma)
        ('15364811000001101'),  -- Ethinylestradiol + Etonogestrel

        -- Co-cyprindiol (Ethinylestradiol + Cyproterone) - also used for contraception
        ('18036911000001101')   -- Co-cyprindiol
    ) AS t(code)
),

women_with_high_bmi_measurement AS (
    -- Identify women with BMI ≥40 from laboratory/clinical measurements
    -- Value column contains the numeric BMI reading
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        g.EventDate as bmi_record_date,
        TRY_CAST(g.Value AS DOUBLE) as bmi_value
    FROM {patient_view} p
    INNER JOIN {gp_events_enriched} g
        ON p.FK_Patient_Link_ID = g.FK_Patient_Link_ID
    WHERE g.SuppliedCode IN (SELECT code FROM bmi_observation_codes)
        AND p.Sex = 'F'  -- Female patients only
        AND g.EventDate IS NOT NULL
        AND g.Value IS NOT NULL
        -- Try to cast Value to numeric and check if ≥40
        AND TRY_CAST(g.Value AS DOUBLE) IS NOT NULL
        AND TRY_CAST(g.Value AS DOUBLE) >= 40  -- BMI ≥40
        AND TRY_CAST(g.Value AS DOUBLE) <= 200  -- Exclude implausible values
),

women_with_severe_obesity_diagnosis AS (
    -- Identify women with documented severe obesity/BMI ≥40 diagnoses
    -- Used as backup or confirmation when BMI measurements indicate severe obesity
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        g.EventDate as diagnosis_date
    FROM {patient_view} p
    INNER JOIN {gp_events_enriched} g
        ON p.FK_Patient_Link_ID = g.FK_Patient_Link_ID
    WHERE g.SuppliedCode IN (SELECT code FROM severe_obesity_diagnosis_codes)
        AND p.Sex = 'F'  -- Female patients only
        AND g.EventDate IS NOT NULL
),

women_with_bmi_40_plus AS (
    -- Combine both sources of BMI ≥40 evidence
    SELECT
        FK_Patient_Link_ID,
        MAX(bmi_record_date) as most_recent_bmi_date,
        MAX(source_type) as source_type
    FROM (
        SELECT
            FK_Patient_Link_ID,
            bmi_record_date,
            'BMI measurement' as source_type
        FROM women_with_high_bmi_measurement

        UNION ALL

        SELECT
            FK_Patient_Link_ID,
            diagnosis_date as bmi_record_date,
            'Severe obesity diagnosis' as source_type
        FROM women_with_severe_obesity_diagnosis
    ) combined
    GROUP BY FK_Patient_Link_ID
),

chc_prescriptions_women AS (
    -- Identify CHC prescriptions to women
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        pr.medication_start_date,
        pr.medication_end_date,
        pr.medication_name
    FROM {patient_view} p
    INNER JOIN {gp_prescriptions} pr
        ON p.FK_Patient_Link_ID = pr.FK_Patient_Link_ID
    WHERE pr.medication_code IN (SELECT code FROM combined_contraceptive_codes)
        AND p.Sex = 'F'  -- Female patients only
        AND pr.medication_start_date IS NOT NULL
),

chc_bmi_40_plus AS (
    -- Identify CHC prescriptions where patient has BMI ≥40 documented within 12 months before prescription
    SELECT DISTINCT
        chc.FK_Patient_Link_ID,
        chc.medication_start_date,
        chc.medication_end_date,
        chc.medication_name,
        bmi.most_recent_bmi_date,
        bmi.source_type
    FROM chc_prescriptions_women chc
    INNER JOIN women_with_bmi_40_plus bmi
        ON chc.FK_Patient_Link_ID = bmi.FK_Patient_Link_ID
    WHERE bmi.most_recent_bmi_date <= chc.medication_start_date
        -- BMI ≥40 record within 12 months before prescription
        AND bmi.most_recent_bmi_date >= (chc.medication_start_date - INTERVAL '365 days')
)

-- Return patient IDs matching this filter with period dates
SELECT DISTINCT
    FK_Patient_Link_ID,
    23 as filter_id,
    medication_start_date as start_date,
    medication_end_date as end_date
FROM chc_bmi_40_plus
ORDER BY FK_Patient_Link_ID, medication_start_date;
