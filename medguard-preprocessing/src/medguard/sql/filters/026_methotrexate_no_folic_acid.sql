-- Filter 026: Methotrexate prescribed without folic acid
-- Description: Prescription of methotrexate without co-prescription of folic acid
-- Category: Medication safety
-- Risk level: 3
--
-- This filter identifies patients who:
-- 1. Have been prescribed oral methotrexate
-- 2. Do NOT have a co-prescribed folic acid supplement during the methotrexate treatment period
--
-- Rationale:
-- - Methotrexate can cause folate deficiency leading to side effects (mouth ulcers, GI symptoms, bone marrow suppression)
-- - Folic acid supplementation (typically 5mg once weekly) reduces methotrexate toxicity without reducing efficacy
-- - Standard practice is to co-prescribe folic acid with methotrexate for inflammatory conditions
--
-- Design decisions:
-- - Check for folic acid prescriptions that overlap with or are prescribed close to methotrexate
-- - Allow folic acid prescriptions that start up to 30 days before or during methotrexate treatment
-- - Include all oral methotrexate formulations (tablets, solutions, suspensions)
-- - Include all folic acid strengths (typically 5mg weekly, but also 400mcg daily)
-- - Folinic acid (calcium folinate) also included as it's used for similar purpose

WITH methotrexate_oral_medication_codes AS (
    -- Reused from filter 054
    SELECT code FROM (VALUES
        -- Methotrexate 2.5mg tablets
        ('965211000001109'), ('1309211000001104'), ('11925811000001104'), ('20310611000001100'),
        ('24381611000001105'), ('383711000001107'), ('683611000001105'), ('706911000001103'),
        ('11026411000001101'), ('21796211000001108'), ('22222311000001101'), ('24136011000001106'),
        ('29918911000001101'), ('34956611000001101'), ('39041011000001109'), ('41149811000001103'),
        ('14709211000001105'), ('14946711000001105'), ('37273211000001103'), ('167911000001107'),
        ('41792011000001100'), -- 2.5mg tablet generic

        -- Methotrexate 10mg tablets
        ('959011000001109'), ('191111000001100'), ('136411000001105'), ('11026611000001103'),
        ('15109411000001107'), ('20310811000001101'), ('20310911000001106'), ('21678811000001107'),
        ('21796511000001106'), ('22222111000001103'), ('24135711000001100'), ('24381411000001107'),
        ('24381511000001106'), ('1945911000001108'), ('14963911000001107'), ('39876411000001106'),
        ('39876611000001109'), ('928011000001103'), ('41791911000001107'), -- 10mg tablet generic

        -- Methotrexate oral solutions (various strengths)
        ('30799911000001104'), ('8664911000001105'), ('8665311000001108'), ('8665811000001104'),
        ('12813911000001109'), ('12814311000001105'), ('12814511000001104'), ('12814711000001109'),
        ('12815211000001101'), ('12815411000001102'), ('12815611000001104'), ('12815811000001100'),
        ('12816911000001103'), ('12817311000001101'), ('12817511000001107'), ('8619311000001106'),
        ('8622711000001105'), ('8625811000001109'), ('8617811000001105'), ('8619811000001102'),
        ('8625711000001101'), ('8619211000001103'), ('8621811000001106'), ('12793911000001105'),
        ('12796011000001100'), ('12796611000001107'), ('12798511000001109'), ('12800811000001109'),
        ('12802111000001103'), ('12802911000001100'), ('12803511000001100'), ('12804411000001101'),
        ('12805611000001102'), ('12806511000001108'), ('21300511000001107'), ('22249211000001104'),
        ('8618111000001102'), ('8619911000001107'), ('8625911000001104'), ('12794011000001105'),
        ('12796111000001104'), ('12796711000001103'), ('12798611000001108'), ('12800911000001104'),
        ('12802211000001109'), ('12803011000001108'), ('12803611000001101'), ('12804611000001103'),
        ('12805711000001106'), ('12806611000001107'), ('12817111000001103'),

        -- Methotrexate oral suspensions (various strengths)
        ('8665011000001105'), ('8665411000001101'), ('8665911000001109'), ('12814011000001107'),
        ('12814411000001103'), ('12814611000001100'), ('12814811000001101'), ('12815011000001106'),
        ('12815311000001109'), ('12815511000001103'), ('12815711000001108'), ('12815911000001105'),
        ('12817011000001104'), ('12817411000001108'), ('8665611000001103'), ('8665711000001107'),
        ('8666011000001101'), ('8666111000001100'), ('8618611000001105'), ('8620211000001104'),
        ('8626211000001102'), ('12793611000001101'), ('12795711000001106'), ('12796311000001102'),
        ('12798111000001100'), ('12800511000001106'), ('12801811000001101'), ('12802511000001107'),
        ('12803211000001103'), ('12803811000001102'), ('12805011000001109'), ('12806211000001105'),
        ('21300511000001107'), ('22249411000001100'), ('8618811000001109'), ('8620311000001107'),
        ('8624211000001107'), ('8626411000001103'), ('8626511000001104'), ('12793711000001105'),
        ('12795811000001103'), ('12796411000001109'), ('12798211000001106'), ('12800611000001105'),
        ('12801911000001106'), ('12802611000001106'), ('12803311000001106'), ('12804011000001105'),
        ('12805111000001105'), ('12806311000001102'), ('12817211000001109'), ('8628711000001108'),
        ('8628811000001100'), ('8628911000001105')
    ) AS t(code)
),

folic_acid_codes AS (
    SELECT code FROM (VALUES
        -- Folic acid tablets (various strengths)
        ('41985411000001106'), -- Folic acid 400mcg tablet
        ('41985311000001104'), -- Folic acid 100mcg tablet
        ('42294611000001109'), -- Folic acid 5mg tablet
        ('19821111000001108'), -- Folic acid 150mg capsules

        -- Folic acid oral solutions and suspensions
        ('8517811000001104'),  -- Folic acid 1mg/5ml oral solution
        ('8517511000001102'),  -- Folic acid 10mg/5ml oral solution
        ('8518011000001106'),  -- Folic acid 300mcg/5ml oral solution
        ('8517611000001103'),  -- Folic acid 10mg/5ml oral suspension
        ('8517911000001109'),  -- Folic acid 1mg/5ml oral suspension
        ('8518111000001107'),  -- Folic acid 300mcg/5ml oral suspension
        ('8518211000001101'),  -- Folic acid 5mg/5ml oral solution
        ('8518411000001102'),  -- Folic acid 5mg/5ml oral suspension
        ('12031711000001100'), -- Folic acid 100mcg/5ml oral solution
        ('12031811000001108'), -- Folic acid 100mcg/5ml oral suspension
        ('12032211000001100'), -- Folic acid 125mcg/5ml oral solution
        ('12032311000001108'), -- Folic acid 125mcg/5ml oral suspension
        ('12032411000001101'), -- Folic acid 150mcg/5ml oral solution
        ('12032611000001103'), -- Folic acid 150mcg/5ml oral suspension
        ('12033011000001101'), -- Folic acid 200mcg/5ml oral solution
        ('12033111000001100'), -- Folic acid 200mcg/5ml oral suspension
        ('12033211000001106'), -- Folic acid 250mcg/5ml oral solution
        ('12033311000001103'), -- Folic acid 250mcg/5ml oral suspension
        ('12033411000001105'), -- Folic acid 25mg/5ml oral solution
        ('12033511000001109'), -- Folic acid 25mg/5ml oral suspension
        ('12033611000001108'), -- Folic acid 2mg/5ml oral solution
        ('12033711000001104'), -- Folic acid 2mg/5ml oral suspension
        ('12033811000001107'), -- Folic acid 400mcg/5ml oral solution
        ('12033911000001102'), -- Folic acid 400mcg/5ml oral suspension
        ('12034011000001104'), -- Folic acid 4mg/5ml oral solution
        ('12034111000001103'), -- Folic acid 4mg/5ml oral suspension
        ('12034211000001109'), -- Folic acid 500mcg/5ml oral solution
        ('12034311000001101'), -- Folic acid 500mcg/5ml oral suspension
        ('12034411000001108'), -- Folic acid 750mcg/5ml oral solution
        ('12034511000001107'), -- Folic acid 750mcg/5ml oral suspension
        ('12032711000001107'), -- Folic acid 2.5mg/5ml oral solution
        ('12032911000001109'), -- Folic acid 2.5mg/5ml oral suspension
        ('12031611000001109'), -- Folic acid 1.5mg/5ml oral suspension
        ('12031511000001105'), -- Folic acid 1.5mg/5ml oral solution
        ('12031911000001103'), -- Folic acid 12.5mg/5ml oral solution
        ('12032011000001105'), -- Folic acid 12.5mg/5ml oral suspension

        -- Folinic acid (calcium folinate) - also used for methotrexate patients
        ('41983011000001103'), -- Calcium folinate 15mg tablet
        ('12289811000001109'), -- Calcium folinate 15mg/5ml oral solution
        ('12289911000001104'), -- Calcium folinate 15mg/5ml oral suspension
        ('12290711000001109'), -- Calcium folinate 7.5mg/5ml oral suspension
        ('12289711000001101'), -- Calcium folinate 12.5mg/5ml oral suspension
        ('12290611000001100'), -- Calcium folinate 7.5mg/5ml oral solution
        ('12289611000001105'), -- Calcium folinate 12.5mg/5ml oral solution
        ('12290011000001107'), -- Calcium folinate 33.333mg/5ml oral solution
        ('12290311000001105'), -- Calcium folinate 37.5mg/5ml oral suspension
        ('12290111000001108'), -- Calcium folinate 33.333mg/5ml oral suspension
        ('12290511000001104'), -- Calcium folinate 6.67mg/5ml oral suspension
        ('12290411000001103'), -- Calcium folinate 6.67mg/5ml oral solution
        ('12290211000001102')  -- Calcium folinate 37.5mg/5ml oral solution
    ) AS t(code)
),

methotrexate_prescriptions AS (
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        pr.medication_start_date,
        pr.medication_end_date,
        pr.medication_name
    FROM {patient_view} p
    INNER JOIN {gp_prescriptions} pr
        ON p.FK_Patient_Link_ID = pr.FK_Patient_Link_ID
    WHERE pr.medication_code IN (SELECT code FROM methotrexate_oral_medication_codes)
        AND pr.medication_start_date IS NOT NULL
),

folic_acid_prescriptions AS (
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        pr.medication_start_date as folic_acid_start_date,
        pr.medication_end_date as folic_acid_end_date
    FROM {patient_view} p
    INNER JOIN {gp_prescriptions} pr
        ON p.FK_Patient_Link_ID = pr.FK_Patient_Link_ID
    WHERE pr.medication_code IN (SELECT code FROM folic_acid_codes)
        AND pr.medication_start_date IS NOT NULL
),

methotrexate_without_folic_acid AS (
    -- Identify methotrexate prescriptions without concurrent folic acid
    SELECT DISTINCT
        mp.FK_Patient_Link_ID,
        mp.medication_start_date,
        mp.medication_end_date,
        mp.medication_name
    FROM methotrexate_prescriptions mp
    WHERE NOT EXISTS (
        SELECT 1
        FROM folic_acid_prescriptions fa
        WHERE fa.FK_Patient_Link_ID = mp.FK_Patient_Link_ID
            -- Folic acid prescription overlaps with or starts near methotrexate
            -- Allow folic acid to start up to 30 days before or during methotrexate treatment
            AND fa.folic_acid_start_date >= (mp.medication_start_date - INTERVAL '30 days')
            -- Folic acid should start before methotrexate ends (or within reasonable extension)
            AND fa.folic_acid_start_date <= COALESCE(mp.medication_end_date, mp.medication_start_date + INTERVAL '90 days')
    )
)

SELECT DISTINCT
    FK_Patient_Link_ID,
    26 as filter_id,
    medication_start_date as start_date,
    medication_end_date as end_date
FROM methotrexate_without_folic_acid
ORDER BY FK_Patient_Link_ID, medication_start_date;
