-- Filter 019: Combined hormonal contraceptive prescribed to woman with history of venous or arterial thromboembolism
--
-- This filter identifies patients who:
-- 1. Are female
-- 2. Have a history of venous thromboembolism (VTE) or arterial thromboembolism (ATE)
-- 3. Are prescribed combined hormonal contraceptives (CHC) after their thromboembolism diagnosis
--
-- Combined hormonal contraceptives include:
-- 1. Combined oral contraceptive pills (COCs) containing estrogen + progestogen
-- 2. Transdermal contraceptive patches (e.g., Evra)
-- 3. Vaginal contraceptive rings (e.g., NuvaRing)
--
-- Thromboembolism history includes:
-- - Venous: Deep vein thrombosis (DVT), pulmonary embolism (PE), other venous thromboembolism
-- - Arterial: Stroke, myocardial infarction, other arterial thrombotic events
--
-- Design decisions:
-- - CHC is absolutely contraindicated in women with history of VTE/ATE (WHO category 4)
-- - Prescription must occur AFTER the thromboembolism diagnosis
-- - Filter restricted to female patients only
-- - Includes all forms of combined hormonal contraception (oral, patch, ring)
-- - UK dm+d codes for all common COC brands and formulations

WITH thromboembolism_codes AS (
    -- IMPORTANT: This list includes codes for venous and arterial thromboembolism
    SELECT code FROM (VALUES
        -- Venous thromboembolism
        ('429098002'),  -- Thromboembolism of vein [PARENT]
        ('1208865003'), -- Embolism of vein from thrombosis of vena cava
        ('1208847002'), -- Venous thromboembolism due to thrombosis of vein of lower limb
        ('1208842008'), -- Thromboembolism of vein due to thrombosis of vein of upper limb
        ('1258883002'), -- Thromboembolus of vein following surgical procedure
        ('1279533009'), -- Thromboembolism of vein due to prolonged immobilisation
        ('428904003'),  -- History of thromboembolism of vein

        -- Deep vein thrombosis
        ('128053003'),  -- Deep venous thrombosis [PARENT]
        ('49956009'),   -- Antepartum deep phlebothrombosis
        ('56272000'),   -- Deep venous thrombosis in puerperium
        ('213220000'),  -- Postoperative deep vein thrombosis
        ('234044007'),  -- Iliofemoral deep vein thrombosis
        ('710167004'),  -- Recurrent deep vein thrombosis
        ('978421000000101'), -- Unprovoked deep vein thrombosis
        ('978441000000108'), -- Provoked deep vein thrombosis
        ('161508001'),  -- History of deep vein thrombosis
        ('164353731000119106'), -- Acute deep vein thrombus during postpartum period
        ('172734791000119103'), -- Postpartum chronic deep vein thrombosis
        ('14534009'),   -- Splenic vein thrombosis
        ('17920008'),   -- Portal vein thrombosis

        -- Pulmonary embolism
        ('59282003'),   -- Pulmonary embolism [PARENT]
        ('194883006'),  -- Postoperative pulmonary embolus
        ('200284000'),  -- Obstetric pulmonary embolism
        ('438773007'),  -- Recurrent pulmonary embolism
        ('441557008'),  -- Septic pulmonary embolism
        ('133971000119108'), -- Chronic pulmonary embolism
        ('706870000'),  -- Acute pulmonary embolism
        ('161512007'),  -- History of pulmonary embolus
        ('200286003'),  -- Obstetric air pulmonary embolism
        ('233936003'),  -- Acute massive pulmonary embolism
        ('233937007'),  -- Subacute massive pulmonary embolism
        ('82153002'),   -- Miscarriage with pulmonary embolism
        ('1001000119102'), -- Pulmonary embolism with pulmonary infarction
        ('10759311000119104'), -- Pulmonary embolism in childbirth
        ('1258896001'), -- Amniotic fluid pulmonary embolism
        ('200299000'),  -- Obstetric pulmonary thromboembolism

        -- Arterial thromboembolism - Stroke
        ('230690007'),  -- Cerebrovascular accident [PARENT]
        ('25133001'),   -- Completed stroke
        ('57981008'),   -- Progressing stroke
        ('111297002'),  -- Nonparalytic stroke
        ('116288000'),  -- Paralytic stroke
        ('230698000'),  -- Lacunar infarction
        ('275526006'),  -- History of cerebrovascular accident
        ('371040005'),  -- Thrombotic stroke
        ('371041009'),  -- Embolic stroke
        ('371121002'),  -- Neonatal stroke
        ('373606000'),  -- Occlusive stroke
        ('413758000'),  -- Cardioembolic stroke
        ('422504002'),  -- Ischaemic stroke
        ('16371781000119100'), -- Cerebellar stroke
        ('16891111000119104'), -- Cryptogenic stroke
        ('769023031000119104'), -- Cerebrovascular accident of thalamus
        ('769211000000103'), -- Suspected cerebrovascular accident
        ('1078001000000105'), -- Haemorrhagic stroke
        ('195212005'),  -- Brainstem stroke syndrome
        ('195213000'),  -- Cerebellar stroke syndrome
        ('230739000'),  -- Spinal cord stroke
        ('281240008'),  -- Extension of cerebrovascular accident
        ('95457000'),   -- Brain stem infarction
        ('426983002'),  -- Infarction of medulla oblongata

        -- Arterial thromboembolism - Myocardial infarction
        ('22298006'),   -- Myocardial infarction [PARENT]
        ('1755008'),    -- Old myocardial infarction
        ('57054005'),   -- Acute myocardial infarction
        ('129574000'),  -- Postoperative myocardial infarction
        ('194856005'),  -- Subsequent myocardial infarction
        ('233843008'),  -- Silent myocardial infarction
        ('394710008'),  -- First myocardial infarction
        ('428752002'),  -- Recent myocardial infarction
        ('399211009'),  -- History of myocardial infarction
        ('52035003'),   -- Acute anteroapical myocardial infarction
        ('62695002')    -- Acute anteroseptal myocardial infarction
    ) AS t(code)
),

women_with_thromboembolism AS (
    -- Identify women with history of thromboembolism
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        MIN(g.EventDate) as earliest_thromboembolism_date
    FROM {patient_view} p
    INNER JOIN {gp_events_enriched} g
        ON p.FK_Patient_Link_ID = g.FK_Patient_Link_ID
    WHERE g.SuppliedCode IN (SELECT code FROM thromboembolism_codes)
        AND p.Sex = 'F'  -- Female patients only
        AND g.EventDate IS NOT NULL
    GROUP BY p.FK_Patient_Link_ID
),

combined_contraceptive_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- These codes match actual UK prescription data
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

women_prescribed_chc_after_thromboembolism AS (
    -- Identify women prescribed CHC after thromboembolism diagnosis
    SELECT DISTINCT
        wt.FK_Patient_Link_ID,
        wt.earliest_thromboembolism_date,
        p.medication_start_date,
        p.medication_end_date,
        p.medication_code,
        p.medication_name
    FROM women_with_thromboembolism wt
    INNER JOIN {gp_prescriptions} p
        ON wt.FK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE p.medication_code IN (SELECT code FROM combined_contraceptive_codes)
        AND p.medication_start_date >= wt.earliest_thromboembolism_date
)

-- Return results
SELECT DISTINCT
    FK_Patient_Link_ID,
    '019' as filter_id,
    medication_start_date as start_date,
    medication_end_date as end_date
FROM women_prescribed_chc_after_thromboembolism;
