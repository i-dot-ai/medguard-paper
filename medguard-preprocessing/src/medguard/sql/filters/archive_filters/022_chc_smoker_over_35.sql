-- Filter 022: Combined hormonal contraceptive prescribed to woman aged ≥35 years who is a current smoker
--
-- This filter identifies patients who:
-- 1. Are female
-- 2. Are aged ≥35 years at time of CHC prescription
-- 3. Have documented current smoker status within 12 months before prescription
-- 4. Are prescribed combined hormonal contraceptives (CHC)
--
-- Combined hormonal contraceptives include:
-- 1. Combined oral contraceptive pills (COCs) containing estrogen + progestogen
-- 2. Transdermal contraceptive patches (e.g., Evra)
-- 3. Vaginal contraceptive rings (e.g., NuvaRing)
--
-- Rationale:
-- - CHC increases risk of cardiovascular events (stroke, MI, VTE)
-- - Smoking increases cardiovascular risk
-- - Combined risk is significantly elevated in women ≥35 years
-- - WHO Medical Eligibility Criteria: CHC in smokers ≥35 is category 3 (<15 cigs/day) or 4 (≥15 cigs/day)
--
-- Design decisions:
-- - Age calculated at time of CHC prescription (must be ≥35 at prescription start)
-- - Smoking status must be documented as "current smoker" within 12 months before prescription
-- - Filter restricted to female patients only
-- - Includes all forms of combined hormonal contraception (oral, patch, ring)
-- - Uses UK dm+d codes for all common COC brands and formulations

WITH current_smoker_codes AS (
    SELECT code FROM (VALUES
        -- Current smoker findings
        ('77176002'),    -- Smoker (finding) [PARENT]
        ('59978006'),    -- Cigar smoker (finding)
        ('65568007'),    -- Cigarette smoker (finding)
        ('82302008'),    -- Pipe smoker (finding)
        ('56578002'),    -- Moderate smoker (20 or less per day) (finding)
        ('56771006'),    -- Heavy smoker (over 20 per day) (finding)
        ('428041000124106'), -- Occasional tobacco smoker (finding)
        ('449868002'),   -- Smokes tobacco daily (finding)
        ('230059006'),   -- Occasional cigarette smoker (finding)
        ('230060001'),   -- Light cigarette smoker (finding)
        ('230062009'),   -- Moderate cigarette smoker (finding)
        ('230063004'),   -- Heavy cigarette smoker (finding)
        ('230064005'),   -- Very heavy cigarette smoker (finding)
        ('160619003'),   -- Rolls own cigarettes (finding)
        ('308438006'),   -- Smoking restarted
        ('266920004'),   -- Trivial cigarette smoker (less than one cigarette/day) (finding)
        ('160603005'),   -- Light cigarette smoker (1-9 cigs/day) (finding)
        ('160604004'),   -- Moderate cigarette smoker (10-19 cigs/day) (finding)
        ('160605003'),   -- Heavy cigarette smoker (20-39 cigs/day) (finding)
        ('230065006'),   -- Chain smoker (finding)
        ('160606002'),   -- Very heavy cigarette smoker (40+ cigs/day) (finding)
        ('266929003')    -- Smoking started
    ) AS t(code)
),

combined_contraceptive_codes AS (
    -- UK SNOMED CT Extension codes (dm+d codes) for combined hormonal contraceptives
    -- Reused from filter 019
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

women_smokers AS (
    -- Identify women with current smoker status recorded
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        g.EventDate as smoking_record_date
    FROM {patient_view} p
    INNER JOIN {gp_events_enriched} g
        ON p.FK_Patient_Link_ID = g.FK_Patient_Link_ID
    WHERE g.SuppliedCode IN (SELECT code FROM current_smoker_codes)
        AND p.Sex = 'F'  -- Female patients only
        AND g.EventDate IS NOT NULL
),

chc_prescriptions_women_35_plus AS (
    -- Identify CHC prescriptions to women aged 35+ at time of prescription
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        pr.medication_start_date,
        pr.medication_end_date,
        pr.medication_name,
        DATE_DIFF('year', p.Dob, pr.medication_start_date) as age_at_prescription
    FROM {patient_view} p
    INNER JOIN {gp_prescriptions} pr
        ON p.FK_Patient_Link_ID = pr.FK_Patient_Link_ID
    WHERE pr.medication_code IN (SELECT code FROM combined_contraceptive_codes)
        AND p.Sex = 'F'  -- Female patients only
        AND p.Dob IS NOT NULL
        AND pr.medication_start_date IS NOT NULL
        AND DATE_DIFF('year', p.Dob, pr.medication_start_date) >= 35
),

chc_smoker_35_plus AS (
    -- Identify CHC prescriptions where patient is 35+, smoker, and smoking status documented within 12 months
    SELECT DISTINCT
        chc.FK_Patient_Link_ID,
        chc.medication_start_date,
        chc.medication_end_date,
        chc.medication_name,
        chc.age_at_prescription
    FROM chc_prescriptions_women_35_plus chc
    INNER JOIN women_smokers ws
        ON chc.FK_Patient_Link_ID = ws.FK_Patient_Link_ID
    WHERE ws.smoking_record_date <= chc.medication_start_date
        -- Smoking record within 12 months before prescription
        AND ws.smoking_record_date >= (chc.medication_start_date - INTERVAL '365 days')
)

SELECT DISTINCT
    FK_Patient_Link_ID,
    '022' as filter_id,
    medication_start_date as start_date,
    medication_end_date as end_date
FROM chc_smoker_35_plus
ORDER BY FK_Patient_Link_ID, medication_start_date;
