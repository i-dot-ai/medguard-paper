-- Filter 033: Concurrent use of warfarin and any antibiotic without monitoring the INR within 5 days
-- Description: Warfarin and antibiotic prescribed concurrently without INR check within 5 days of antibiotic start
-- Category: Drug monitoring
-- Risk level: 3
--
-- This filter identifies patients who:
-- 1. Have concurrent prescriptions for warfarin and an antibiotic (overlapping prescription periods)
-- 2. Do NOT have an INR check recorded within 5 days of the antibiotic prescription start date
--
-- Rationale:
-- - Many antibiotics interact with warfarin, increasing INR and bleeding risk
-- - Mechanism: altered gut flora reducing vitamin K production, or enzyme inhibition
-- - High-risk interactions: clarithromycin, erythromycin, ciprofloxacin, metronidazole, co-amoxiclav
-- - Moderate risk: amoxicillin, flucloxacillin, cefalexin, doxycycline, trimethoprim
-- - INR should be checked within 5 days of starting antibiotic to detect changes
--
-- Design decisions:
-- - Antibiotic must overlap with warfarin prescription (concurrent use)
-- - INR check should occur within 5 days AFTER antibiotic start (inclusive of start date)
-- - Includes common oral antibiotics (systemic formulations)
-- - Excludes topical/eye/ear preparations (minimal systemic absorption)
-- - Focus on tablet/capsule/suspension formulations

WITH warfarin_codes AS (
    SELECT code FROM (VALUES
        -- Warfarin tablets (all strengths)
        ('42217611000001104'), -- Warfarin 3mg tablet
        ('42217711000001108'), -- Warfarin 4mg tablet
        ('42217911000001105'), -- Warfarin 5mg tablet
        ('42217511000001103'), -- Warfarin 1mg tablet
        ('42217811000001100'), -- Warfarin 500mcg tablet
        ('32751111000001103'), -- Warfarin 1mg capsules
        ('32751211000001109'), -- Warfarin 3mg capsules
        ('32751311000001101'), -- Warfarin 5mg capsules

        -- Warfarin oral solutions
        ('8797911000001107'),  -- Warfarin 10mg/5ml oral solution
        ('8798011000001109'),  -- Warfarin 10mg/5ml oral suspension
        ('8798511000001101'),  -- Warfarin 3mg/5ml oral solution
        ('8798611000001102'),  -- Warfarin 3mg/5ml oral suspension
        ('8798711000001106'),  -- Warfarin 5mg/5ml oral solution
        ('8798811000001103'),  -- Warfarin 5mg/5ml oral suspension
        ('8798111000001105'),  -- Warfarin 1mg/5ml oral solution
        ('8798211000001104'),  -- Warfarin 1mg/5ml oral suspension
        ('8798311000001107'),  -- Warfarin 2mg/5ml oral solution
        ('8798411000001100')   -- Warfarin 2mg/5ml oral suspension
    ) AS t(code)
),

antibiotic_codes AS (
    -- Common oral antibiotics that interact with warfarin
    SELECT code FROM (VALUES
        -- Amoxicillin (moderate interaction)
        ('39732411000001106'), -- Amoxicillin 500mg capsule
        ('39732311000001104'), -- Amoxicillin 250mg capsule
        ('44456411000001100'), -- Amoxicillin 500mg tablet

        -- Co-amoxiclav/Augmentin (high interaction)
        ('9569701000001100'),  -- Augmentin
        ('9574301000001105'),  -- Augmentin
        ('94411000001100'),    -- Augmentin 375mg tablets
        ('292511000001103'),   -- Augmentin 625mg tablets

        -- Flucloxacillin (moderate interaction)
        ('39692211000001107'), -- Flucloxacillin 500mg capsule
        ('39692111000001101'), -- Flucloxacillin 250mg capsule

        -- Cefalexin (moderate interaction)
        ('39694811000001102'), -- Cefalexin 500mg capsule
        ('39735311000001105'), -- Cefalexin 250mg capsule
        ('39684111000001105'), -- Cefalexin 250mg tablet
        ('39735911000001106'), -- Cefalexin 500mg tablet

        -- Clarithromycin (high interaction - enzyme inhibitor)
        ('41946511000001109'), -- Clarithromycin 500mg tablet
        ('41946311000001103'), -- Clarithromycin 250mg tablet

        -- Erythromycin (high interaction - enzyme inhibitor)
        ('41949311000001105'), -- Erythromycin stearate 250mg tablet
        ('41949411000001103'), -- Erythromycin stearate 500mg tablet
        ('41949111000001108'), -- Erythromycin ethyl succinate 500mg tablet
        ('41948811000001108'), -- Erythromycin 250mg gastro-resistant tablet

        -- Azithromycin (moderate interaction)
        ('39733511000001103'), -- Azithromycin 500mg tablet
        ('41942011000001100'), -- Azithromycin 250mg capsule

        -- Doxycycline (moderate interaction)
        ('41948411000001106'), -- Doxycycline 100mg tablet
        ('41948311000001104'), -- Doxycycline 100mg capsule
        ('41948611000001109'), -- Doxycycline 50mg capsule
        ('41948511000001105'), -- Doxycycline 20mg tablet

        -- Trimethoprim (moderate interaction)
        ('41956211000001109'), -- Trimethoprim 200mg tablet
        ('41956111000001103'), -- Trimethoprim 100mg tablet

        -- Ciprofloxacin (high interaction)
        ('39687811000001107'), -- Ciprofloxacin 500mg tablet
        ('39687511000001109'), -- Ciprofloxacin 250mg tablet
        ('39686211000001109'), -- Ciprofloxacin 100mg tablet
        ('39687011000001101'), -- Ciprofloxacin 750mg tablet

        -- Metronidazole (high interaction - enzyme inhibitor)
        ('41952111000001102'), -- Metronidazole 400mg tablet
        ('41951911000001105'), -- Metronidazole 200mg tablet
        ('41952311000001100')  -- Metronidazole 500mg tablet
    ) AS t(code)
),

inr_codes AS (
    SELECT code FROM (VALUES
        -- INR measurement procedures and findings
        ('1951000175101'),   -- International normalised ratio
        ('313341008'),       -- INR above reference range
        ('1285280000'),      -- INR below reference range
        ('165583001'),       -- INR outside reference range
        ('737113001'),       -- INR calculation technique
        ('413086003'),       -- Deviation of INR from target range
        ('165582006')        -- INR within reference range
    ) AS t(code)
),

warfarin_prescriptions AS (
    SELECT DISTINCT
        gp.FK_Patient_Link_ID,
        gp.medication_start_date as warfarin_start_date,
        gp.medication_end_date as warfarin_end_date,
        gp.medication_name as warfarin_name
    FROM {gp_prescriptions} gp
    INNER JOIN warfarin_codes wc ON gp.medication_code = wc.code
    WHERE gp.medication_start_date IS NOT NULL
),

antibiotic_prescriptions AS (
    SELECT DISTINCT
        gp.FK_Patient_Link_ID,
        gp.medication_start_date as antibiotic_start_date,
        gp.medication_end_date as antibiotic_end_date,
        gp.medication_name as antibiotic_name
    FROM {gp_prescriptions} gp
    INNER JOIN antibiotic_codes ac ON gp.medication_code = ac.code
    WHERE gp.medication_start_date IS NOT NULL
),

inr_checks AS (
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        ge.EventDate as inr_check_date
    FROM {gp_events_enriched} ge
    INNER JOIN inr_codes ic ON ge.SuppliedCode = ic.code
    WHERE ge.EventDate IS NOT NULL
),

concurrent_warfarin_antibiotic AS (
    -- Identify concurrent warfarin and antibiotic use
    SELECT DISTINCT
        wp.FK_Patient_Link_ID,
        wp.warfarin_start_date,
        wp.warfarin_end_date,
        wp.warfarin_name,
        ap.antibiotic_start_date,
        ap.antibiotic_end_date,
        ap.antibiotic_name
    FROM warfarin_prescriptions wp
    INNER JOIN antibiotic_prescriptions ap
        ON wp.FK_Patient_Link_ID = ap.FK_Patient_Link_ID
    WHERE
        -- Antibiotic overlaps with warfarin prescription
        ap.antibiotic_start_date <= COALESCE(wp.warfarin_end_date, wp.warfarin_start_date + INTERVAL '90 days')
        AND COALESCE(ap.antibiotic_end_date, ap.antibiotic_start_date + INTERVAL '14 days') >= wp.warfarin_start_date
),

warfarin_antibiotic_no_inr AS (
    -- Identify concurrent use WITHOUT INR check within 5 days of antibiotic start
    SELECT DISTINCT
        cwa.FK_Patient_Link_ID,
        cwa.warfarin_start_date,
        cwa.warfarin_end_date,
        cwa.warfarin_name,
        cwa.antibiotic_start_date,
        cwa.antibiotic_end_date,
        cwa.antibiotic_name
    FROM concurrent_warfarin_antibiotic cwa
    WHERE NOT EXISTS (
        SELECT 1
        FROM inr_checks ic
        WHERE ic.FK_Patient_Link_ID = cwa.FK_Patient_Link_ID
            -- INR check on same day as antibiotic start OR within 5 days after
            AND ic.inr_check_date >= cwa.antibiotic_start_date
            AND ic.inr_check_date <= (cwa.antibiotic_start_date + INTERVAL '5 days')
    )
)

SELECT DISTINCT
    FK_Patient_Link_ID,
    33 AS filter_id,
    antibiotic_start_date AS start_date,
    antibiotic_end_date AS end_date
FROM warfarin_antibiotic_no_inr
ORDER BY FK_Patient_Link_ID, antibiotic_start_date;
