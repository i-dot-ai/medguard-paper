-- Filter 051: Lithium prescription without level monitoring
-- Description: Prescription of lithium without a record of a lithium level being measured within the previous 6 months
-- Category: Laboratory test monitoring
-- Risk level: 3
-- PINCER: secondary
--
-- This filter identifies patients who:
-- 1. Have been prescribed lithium (carbonate or citrate formulations)
-- 2. Do NOT have a recorded lithium level measurement within the previous 6 months (180 days) before prescription start

WITH lithium_medication_codes AS (
    SELECT code FROM (VALUES
        -- Lithium carbonate tablets
        ('963211000001105'), -- Lithium carbonate 250mg tablets
        ('30760011000001108'), -- Lithium carbonate 250mg tablets (Essential Pharma)
        ('30760111000001109'), -- Lithium carbonate 250mg tablets (Essential Pharma) 100 tablet
        ('30802011000001105'), -- Lithium carbonate 250mg tablets (Alliance Healthcare)
        ('30802211000001100'), -- Lithium carbonate 250mg tablets (Alliance Healthcare) 100 tablet
        ('30988111000001104'), -- Lithium carbonate 250mg tablets (A A H Pharmaceuticals)
        ('30988211000001105'), -- Lithium carbonate 250mg tablets (A A H Pharmaceuticals) 100 tablet
        ('42295711000001101'), -- Lithium carbonate 250mg conventional release oral tablet

        -- Lithium carbonate modified-release tablets
        ('1114411000001108'), -- Lithium carbonate 200mg modified-release tablets 100 tablet
        ('1269111000001100'), -- Lithium carbonate 400mg modified-release tablets 100 tablet
        ('1306011000001103'), -- Lithium carbonate 450mg modified-release tablets 60 tablet
        ('36040211000001104'), -- Lithium carbonate 450mg modified-release tablets
        ('39110011000001104'), -- Lithium carbonate 200mg modified-release oral tablet
        ('39110111000001103'), -- Lithium carbonate 400mg modified-release oral tablet
        ('4818611000001104'), -- Lithium carbonate 400mg modified-release tablets (Kent Pharma)
        ('4818711000001108'), -- Lithium carbonate 400mg modified-release tablets (Kent Pharma) 100 tablet

        -- Lithium carbonate oral suspension
        ('8658611000001103'), -- Lithium carbonate 200mg/5ml oral suspension
        ('8628811000001100'), -- Lithium carbonate 200mg/5ml oral suspension (Special Order)
        ('8628711000001108'), -- Lithium carbonate 200mg/5ml oral suspension 1 ml
        ('8628911000001105'), -- Lithium carbonate 200mg/5ml oral suspension (Special Order) 1 ml

        -- Lithium citrate modified-release tablets
        ('4559411000001104'), -- Lithium citrate 564mg modified-release tablets
        ('4543211000001102'), -- Lithium citrate 564mg modified-release tablets 100 tablet

        -- Lithium citrate oral solution
        ('3832111000001104'), -- Lithium citrate 520mg/5ml oral solution sugar free 150 ml
        ('36040311000001107'), -- Lithium citrate 520mg/5ml oral solution sugar free
        ('4888511000001101'), -- Lithium citrate 1.018g/5ml oral solution 150 ml
        ('8788611000001101'), -- Lithium citrate 509mg/5ml oral solution 150 ml
        ('42295811000001109'), -- Lithium citrate 203.6mg/ml conventional release oral solution 5ml spoonful
        ('42295911000001104'), -- Lithium citrate 101.8mg/ml conventional release oral solution 5ml spoonful

        -- Brand names
        ('9311401000001108'), -- Priadel (lithium carbonate)
        ('9311501000001107')  -- Priadel (lithium citrate)
    ) AS t(code)
),

lithium_level_codes AS (
    SELECT code FROM (VALUES
        -- Measurement procedures
        ('54392006'), -- Lithium measurement (procedure)
        ('269871000'), -- Serum lithium measurement (procedure)
        ('271267007'), -- Urine lithium measurement (procedure)

        -- Findings and results
        ('365738002'), -- Finding of lithium level (finding)
        ('365739005'), -- Finding of blood lithium level (finding)
        ('365740007'), -- Finding of serum lithium level (finding)
        ('1006681000000100'), -- Serum lithium level
        ('1089391000000104'), -- Blood lithium level (observable entity)

        -- Therapeutic range findings
        ('166956002'), -- Lithium level therapeutic (finding)
        ('166957006'), -- Lithium level high - toxic (finding)
        ('166958001'), -- Lithium level below therapeutic range
        ('442174001'), -- Lithium in blood specimen outside therapeutic range (finding)
        ('1156020005'), -- Serum lithium level within therapeutic range
        ('1156021009'), -- Serum lithium level above therapeutic range
        ('1156022002'), -- Serum lithium level below therapeutic range (finding)

        -- Monitoring documentation
        ('755361000000103'), -- Lithium level checked at 3 monthly intervals
        ('1362011000000102')  -- Lithium level checked at 6 monthly intervals (finding)
    ) AS t(code)
),

lithium_prescriptions AS (
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        pr.medication_start_date,
        pr.medication_end_date,
        pr.medication_name
    FROM {patient_view} p
    INNER JOIN {gp_prescriptions} pr
        ON p.FK_Patient_Link_ID = pr.FK_Patient_Link_ID
    WHERE pr.medication_code IN (SELECT code FROM lithium_medication_codes)
        AND pr.medication_start_date IS NOT NULL
),

lithium_level_checks AS (
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        g.EventDate as level_check_date
    FROM {patient_view} p
    INNER JOIN {gp_events_enriched} g
        ON p.FK_Patient_Link_ID = g.FK_Patient_Link_ID
    WHERE g.SuppliedCode IN (SELECT code FROM lithium_level_codes)
        AND g.EventDate IS NOT NULL
),

prescriptions_without_recent_level_check AS (
    SELECT DISTINCT
        lp.FK_Patient_Link_ID,
        lp.medication_start_date,
        lp.medication_end_date,
        lp.medication_name
    FROM lithium_prescriptions lp
    WHERE NOT EXISTS (
        SELECT 1
        FROM lithium_level_checks llc
        WHERE llc.FK_Patient_Link_ID = lp.FK_Patient_Link_ID
            AND llc.level_check_date >= (lp.medication_start_date - INTERVAL '180 days')
            AND llc.level_check_date <= lp.medication_start_date
    )
)

SELECT DISTINCT
    FK_Patient_Link_ID,
    '051' as filter_id,
    medication_start_date as start_date,
    medication_end_date as end_date
FROM prescriptions_without_recent_level_check;
