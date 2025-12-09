-- Filter 055: Methotrexate prescription without LFT monitoring
-- Description: Prescription of methotrexate without a record of liver function having been measured within the previous 3 months
-- Category: Laboratory test monitoring
-- Risk level: 3
-- PINCER: secondary
--
-- This filter identifies patients who:
-- 1. Have been prescribed oral methotrexate
-- 2. Do NOT have a recorded liver function test (LFT) within the previous 3 months (90 days) before prescription start

WITH methotrexate_oral_medication_codes AS (
    SELECT code FROM (VALUES
        -- Methotrexate 2.5mg tablets
        ('965211000001109'), ('1309211000001104'), ('11925811000001104'), ('20310611000001100'),
        ('24381611000001105'), ('383711000001107'), ('683611000001105'), ('706911000001103'),
        ('11026411000001101'), ('21796211000001108'), ('22222311000001101'), ('24136011000001106'),
        ('29918911000001101'), ('34956611000001101'), ('39041011000001109'), ('41149811000001103'),
        ('14709211000001105'), ('14946711000001105'), ('37273211000001103'), ('167911000001107'),
        ('41792011000001100'),

        -- Methotrexate 10mg tablets
        ('959011000001109'), ('191111000001100'), ('136411000001105'), ('11026611000001103'),
        ('15109411000001107'), ('20310811000001101'), ('20310911000001106'), ('21678811000001107'),
        ('21796511000001106'), ('22222111000001103'), ('24135711000001100'), ('24381411000001107'),
        ('24381511000001106'), ('1945911000001108'), ('14963911000001107'), ('39876411000001106'),
        ('39876611000001109'), ('928011000001103'), ('41791911000001107'),

        -- Methotrexate oral solutions/suspensions
        ('30799911000001104'), ('8664911000001105'), ('8665011000001105'), ('8665311000001108'),
        ('8665411000001101'), ('8665611000001103'), ('8665711000001107'), ('8665811000001104'),
        ('8665911000001109'), ('8666011000001101'), ('8666111000001100'), ('12813911000001109'),
        ('12814011000001107'), ('12814111000001108'), ('12814211000001102'), ('12814311000001105'),
        ('12814411000001103'), ('12814511000001104'), ('12814611000001100'), ('12814711000001109'),
        ('12814811000001101'), ('12814911000001106'), ('12815011000001106'), ('12815111000001107'),
        ('12815211000001101'), ('12815311000001109'), ('12815411000001102'), ('12815511000001103'),
        ('12815611000001104'), ('12815711000001108'), ('12815811000001100'), ('12815911000001105'),
        ('12816911000001103'), ('12817011000001104'), ('12817111000001103'), ('12817211000001109'),
        ('12817311000001101'), ('12817411000001108'), ('12817511000001107'), ('8617811000001105'),
        ('8618111000001102'), ('8618611000001105'), ('8618811000001109'), ('8619211000001103'),
        ('8619311000001106'), ('8619511000001100'), ('8619611000001101'), ('8619811000001102'),
        ('8619911000001107'), ('8620211000001104'), ('8620311000001107'), ('8621811000001106'),
        ('8622711000001105'), ('8623611000001106'), ('8624211000001107'), ('8625611000001105'),
        ('8625711000001101'), ('8625811000001109'), ('8625911000001104'), ('8626211000001102'),
        ('8626311000001105'), ('8626411000001103'), ('8626511000001104'), ('12793611000001101'),
        ('12793711000001105'), ('12793911000001107'), ('12794011000001105'), ('12795711000001106'),
        ('12795811000001103'), ('12796011000001100'), ('12796111000001104'), ('12796311000001102'),
        ('12796411000001109'), ('12796611000001107'), ('12796711000001103'), ('12798111000001100'),
        ('12798211000001106'), ('12798511000001109'), ('12798611000001108'), ('12800511000001106'),
        ('12800611000001105'), ('12800811000001109'), ('12800911000001104'), ('12801811000001101'),
        ('12801911000001106'), ('12802111000001103'), ('12802211000001109'), ('12802511000001107'),
        ('12802611000001106'), ('12802911000001100'), ('12803011000001108'), ('12803211000001103'),
        ('12803311000001106'), ('12803511000001100'), ('12803611000001101'), ('12803811000001102'),
        ('12804011000001105'), ('12804411000001101'), ('12804611000001103'), ('12805011000001109'),
        ('12805111000001105'), ('12805611000001102'), ('12805711000001106'), ('12806211000001105'),
        ('12806311000001102'), ('12806511000001108'), ('12806611000001107'), ('21300511000001107'),
        ('22249211000001104'), ('22249411000001100'), ('8628711000001108'), ('8628811000001100'),
        ('8628911000001105')
    ) AS t(code)
),

liver_function_test_codes AS (
    SELECT code FROM (VALUES
        -- Liver function test panels
        ('26958001'), -- Hepatic function panel (procedure)
        ('997531000000108'), -- Liver function test
        ('1031081000000108'), -- Liver function tests
        ('166602006'), -- Liver function tests within reference range
        ('166603001'), -- Liver function tests outside reference range
        ('863927004'), -- Liver function test above reference range

        -- Alanine aminotransferase (ALT)
        ('56935002'), -- Alanine aminotransferase (substance)
        ('34608000'), -- Alanine aminotransferase measurement (procedure)
        ('390961000'), -- Plasma alanine aminotransferase level
        ('250637003'), -- Alanine aminotransferase - blood measurement
        ('364571000119101'), -- Alanine transaminase in serum
        ('201321000000108'), -- Serum alanine aminotransferase level
        ('1013211000000103'), -- Plasma alanine aminotransferase level
        ('1018251000000107'), -- Serum alanine aminotransferase level
        ('166646003'), -- Alanine aminotransferase outside reference range
        ('409673008'), -- Alanine aminotransferase above reference range
        ('166645004'), -- Alanine aminotransferase level within reference range
        ('1162723004'), -- Alanine aminotransferase below reference range

        -- Aspartate aminotransferase (AST)
        ('26091008'), -- Aspartate aminotransferase (substance)
        ('45896001'), -- Aspartate aminotransferase measurement (procedure)
        ('373679006'), -- Aspartate transaminase level
        ('1031101000000102'), -- Aspartate aminotransferase level
        ('250641004'), -- Aspartate aminotransferase serum measurement
        ('1000881000000102'), -- Serum aspartate aminotransferase level
        ('166669000'), -- Aspartate aminotransferase serum level above reference range
        ('166668008'), -- Serum aspartate aminotransferase level outside reference range
        ('166667003'), -- AST/SGOT level within reference range

        -- Bilirubin
        ('79706000'), -- Bilirubin (substance)
        ('302787001'), -- Bilirubin measurement (procedure)
        ('359986008'), -- Bilirubin, total measurement (procedure)
        ('365786009'), -- Finding of bilirubin level (finding)
        ('413054008'), -- Bilirubin profile
        ('1021751000000102'), -- Bilirubin profile
        ('26165005'), -- Bilirubin level above reference range
        ('39748002'), -- Bilirubin, direct measurement (procedure)
        ('166610007'), -- Serum bilirubin measurement (procedure)
        ('166611006'), -- Serum bilirubin within reference range
        ('166612004'), -- Serum bilirubin above reference range
        ('365787000'), -- Finding of serum bilirubin level

        -- Alkaline phosphatase (ALP)
        ('57056007'), -- Alkaline phosphatase (substance)
        ('88810008'), -- Alkaline phosphatase measurement (procedure)
        ('274770006'), -- Alkaline phosphatase above reference range
        ('365771003'), -- Finding of alkaline phosphatase level
        ('889401000000102'), -- Measurement of alkaline phosphatase activity

        -- Gamma-glutamyltransferase (GGT)
        ('60153001'), -- Gamma-glutamyltransferase (substance)
        ('313849004'), -- Serum gamma-glutamyl transferase measurement
        ('313850004') -- Plasma gamma-glutamyl transferase measurement
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

liver_function_checks AS (
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        g.EventDate as lft_check_date
    FROM {patient_view} p
    INNER JOIN {gp_events_enriched} g
        ON p.FK_Patient_Link_ID = g.FK_Patient_Link_ID
    WHERE g.SuppliedCode IN (SELECT code FROM liver_function_test_codes)
        AND g.EventDate IS NOT NULL
),

prescriptions_without_recent_lft AS (
    SELECT DISTINCT
        mp.FK_Patient_Link_ID,
        mp.medication_start_date,
        mp.medication_end_date,
        mp.medication_name
    FROM methotrexate_prescriptions mp
    WHERE NOT EXISTS (
        SELECT 1
        FROM liver_function_checks lfc
        WHERE lfc.FK_Patient_Link_ID = mp.FK_Patient_Link_ID
            AND lfc.lft_check_date >= (mp.medication_start_date - INTERVAL '90 days')
            AND lfc.lft_check_date <= mp.medication_start_date
    )
)

SELECT DISTINCT
    FK_Patient_Link_ID,
    55 as filter_id,
    medication_start_date as start_date,
    medication_end_date as end_date
FROM prescriptions_without_recent_lft;
