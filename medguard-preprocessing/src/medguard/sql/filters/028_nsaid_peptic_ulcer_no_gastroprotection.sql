-- Filter 028: NSAID prescribed to patient with history of peptic ulceration without co-prescription of ulcer-healing drug
--
-- This filter identifies patients who:
-- 1. Have a recorded diagnosis of peptic ulcer (including gastric ulcer, duodenal ulcer, etc.)
-- 2. Have been prescribed an NSAID after their peptic ulcer diagnosis
-- 3. Do NOT have a co-prescribed ulcer-healing drug during the NSAID prescription period
--
-- Ulcer-healing drugs include:
-- - Proton pump inhibitors (PPIs): omeprazole, lansoprazole, pantoprazole, esomeprazole, rabeprazole
-- - H2 receptor antagonists: ranitidine, famotidine, cimetidine, nizatidine
--
-- Design decisions:
-- - Uses GP Events for peptic ulcer diagnosis (most specific clinical codes)
-- - Uses GP Prescriptions table for medication prescriptions (consolidated prescription islands)
-- - Co-prescription defined as: ulcer-healing drug with overlapping dates (start/end dates overlap with NSAID dates)
-- - Looks for any peptic ulcer diagnosis in patient history
-- - Excludes selective COX-2 inhibitors as they have lower GI risk
-- - Prioritizes precision: only flags clear cases of NSAID without gastroprotection

WITH peptic_ulcer_codes AS (
    -- SNOMED codes for peptic ulcer and all descendants
    -- Based on concept_id 13200003 (Peptic ulcer disorder)
    SELECT code FROM (VALUES
        ('13200003'),   -- Peptic ulcer (disorder)
        ('196682000'),  -- Acute peptic ulcer (disorder)
        ('109813002'),  -- Drug-induced peptic ulcer (disorder)
        ('128287004'),  -- Chronic peptic ulcer (disorder)
        ('37442009'),   -- Peptic ulcer without hemorrhage/perforation
        ('51868009'),   -- Ulcer of duodenum
        ('64121000'),   -- Peptic ulcer with hemorrhage (disorder)
        ('88169003'),   -- Peptic ulcer with perforation (disorder)
        ('397825006'),  -- Gastric ulcer
        ('95529005'),   -- Acute gastric ulcer (disorder)
        ('95530000'),   -- Chronic gastric ulcer (disorder)
        ('196652006'),  -- Acute duodenal ulcer (disorder)
        ('128286008'),  -- Chronic duodenal ulcer (disorder)
        ('415623008'),  -- Stress ulcer
        ('713638002'),  -- Gastric ulcer caused by drug
        ('724529001')   -- Duodenal ulcer caused by drug
    ) AS t(code)
),

nsaid_codes AS (
    -- SNOMED codes for NSAIDs (non-selective only, excluding COX-2 inhibitors)
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- EXCLUDES topical formulations (gels, creams, foams, sprays, lozenges) with minimal systemic absorption
    SELECT code FROM (VALUES
        -- Parent/international codes (substance level)
        ('372665008'),  -- Non-steroidal anti-inflammatory agent (parent)
        ('387207008'),  -- Ibuprofen
        ('372588000'),  -- Naproxen
        ('7034005'),    -- Diclofenac
        ('373513008'),  -- Indometacin
        ('387153005'),  -- Piroxicam
        ('387185008'),  -- Mefenamic acid
        ('386832008'),  -- Ketoprofen
        ('373506008'),  -- Flurbiprofen
        ('387513000'),  -- Sulindac
        ('391703003'),  -- Aceclofenac

        -- UK dm+d codes: Ibuprofen products (SYSTEMIC ONLY - tablets, capsules)
        ('42104911000001104'),  -- Ibuprofen 400mg tablet
        ('42104811000001109'),  -- Ibuprofen 200mg tablet
        ('42104711000001101'),  -- Ibuprofen 200mg capsule
        ('42105311000001101'),  -- Ibuprofen 600mg tablet
        ('42105411000001108'),  -- Ibuprofen 800mg tablet
        ('10774611000001104'),  -- Ibuprofen 400mg capsules
        -- EXCLUDED: Ibuprofen topicals (gels, foams, creams, sprays) - minimal systemic absorption

        -- UK dm+d codes: Naproxen products
        ('42107811000001100'),  -- Naproxen 500mg tablet
        ('42107511000001103'),  -- Naproxen 250mg tablet
        ('42107711000001108'),  -- Naproxen 500mg suppository
        ('42107911000001105'),  -- Naproxen sodium 275mg tablet
        ('36030111000001106'),  -- Naproxen 500mg modified-release tablets

        -- UK dm+d codes: Diclofenac products (SYSTEMIC ONLY)
        ('42101711000001104'),  -- Diclofenac potassium 50mg tablet
        ('42101611000001108'),  -- Diclofenac potassium 25mg tablet
        ('42101511000001109'),  -- Diclofenac sodium 50mg suppository
        ('42101411000001105'),  -- Diclofenac sodium 25mg suppository
        ('42101311000001103'),  -- Diclofenac sodium 100mg suppository
        -- EXCLUDED: Diclofenac gels (1%, 3%) - minimal systemic absorption

        -- UK dm+d codes: Indometacin products
        ('42105811000001105'),  -- Indometacin 50mg capsule
        ('42105611000001106'),  -- Indometacin 25mg capsule
        ('42105511000001107'),  -- Indometacin 100mg suppository
        ('39024911000001108'),  -- Indometacin 25mg modified-release capsule
        ('42105711000001102'),  -- Indometacin 25mg/5ml oral suspension
        ('8561611000001108'),   -- Indometacin 25mg/5ml oral solution
        ('8561811000001107'),   -- Indometacin 50mg/5ml oral solution
        ('8561911000001102'),   -- Indometacin 50mg/5ml oral suspension

        -- UK dm+d codes: Piroxicam products (SYSTEMIC ONLY)
        ('42110211000001103'),  -- Piroxicam 20mg capsule
        ('42110111000001109'),  -- Piroxicam 10mg capsule
        ('42110311000001106'),  -- Piroxicam 20mg suppository
        ('39721211000001103'),  -- Piroxicam 20mg tablet for suspension
        ('39721011000001108'),  -- Piroxicam 10mg tablet for suspension
        ('3439011000001103'),   -- Piroxicam betadex 20mg tablets
        -- EXCLUDED: Piroxicam 0.5% gel - minimal systemic absorption

        -- UK dm+d codes: Mefenamic acid products
        ('42106311000001106'),  -- Mefenamic acid 250mg capsule
        ('42106411000001104'),  -- Mefenamic acid 500mg tablet
        ('41391311000001107'),  -- Mefenamic acid 250mg tablet
        ('8662311000001102'),   -- Mefenamic acid 250mg/5ml oral suspension
        ('8662411000001109'),   -- Mefenamic acid 500mg/5ml oral suspension

        -- UK dm+d codes: Ketoprofen products (SYSTEMIC ONLY)
        ('42106011000001108'),  -- Ketoprofen 50mg capsule
        ('42105911000001100'),  -- Ketoprofen 100mg suppository
        ('3377811000001108'),   -- Ketoprofen 100mg capsules
        -- EXCLUDED: Ketoprofen gels (10%, 2.5%) - minimal systemic absorption

        -- UK dm+d codes: Flurbiprofen products (SYSTEMIC ONLY)
        ('42104311000001100'),  -- Flurbiprofen 50mg tablet
        ('42104211000001108'),  -- Flurbiprofen 100mg tablet
        ('42104111000001102'),  -- Flurbiprofen 100mg suppository
        -- EXCLUDED: Flurbiprofen 8.75mg lozenges - for sore throat, minimal systemic absorption

        -- UK dm+d codes: Aceclofenac products
        ('42099211000001100'),  -- Aceclofenac 100mg tablet

        -- UK dm+d codes: Sulindac products
        ('42111711000001102'),  -- Sulindac 200mg tablet
        ('42111611000001106')   -- Sulindac 100mg tablet
    ) AS t(code)
),

ulcer_healing_drug_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- Includes both PPIs and H2 receptor antagonists
    SELECT code FROM (VALUES
        -- Parent/international codes - PPIs
        ('372525000'),  -- Proton pump inhibitor (parent)
        ('387137007'),  -- Omeprazole
        ('386888004'),  -- Lansoprazole
        ('395821003'),  -- Pantoprazole
        ('396047003'),  -- Esomeprazole
        ('422225001'),  -- Rabeprazole

        -- Parent/international codes - H2 antagonists
        ('108478009'),  -- Ranitidine
        ('387567009'),  -- Famotidine
        ('373541007'),  -- Cimetidine
        ('387555009'),  -- Nizatidine

        -- UK dm+d codes: Omeprazole products
        ('42356511000001103'),  -- Omeprazole 20mg gastro-resistant tablet
        ('42356311000001109'),  -- Omeprazole 10mg gastro-resistant tablet
        ('42356711000001108'),  -- Omeprazole 40mg gastro-resistant tablet
        ('42356411000001102'),  -- Omeprazole 20mg gastro-resistant capsule
        ('42356211000001101'),  -- Omeprazole 10mg gastro-resistant capsule
        ('42356611000001104'),  -- Omeprazole 40mg gastro-resistant capsule
        ('39021511000001103'),  -- Omeprazole (as magnesium) 20mg gastro-resistant tablet
        ('39021411000001102'),  -- Omeprazole (as magnesium) 10mg gastro-resistant tablet
        ('39021611000001104'),  -- Omeprazole (as magnesium) 40mg gastro-resistant tablet

        -- UK dm+d codes: Lansoprazole products
        ('42354611000001108'),  -- Lansoprazole 30mg gastro-resistant capsule
        ('42354511000001109'),  -- Lansoprazole 15mg gastro-resistant capsule

        -- UK dm+d codes: Pantoprazole products
        ('42357111000001105'),  -- Pantoprazole 40mg gastro-resistant tablet
        ('42357011000001109'),  -- Pantoprazole 20mg gastro-resistant tablet

        -- UK dm+d codes: Esomeprazole products
        ('42353811000001109'),  -- Esomeprazole 40mg gastro-resistant tablet
        ('42353711000001101'),  -- Esomeprazole 20mg gastro-resistant tablet
        ('17631411000001100'),  -- Esomeprazole 40mg gastro-resistant capsules
        ('17631311000001107'),  -- Esomeprazole 20mg gastro-resistant capsules

        -- UK dm+d codes: Rabeprazole products
        ('42357511000001101'),  -- Rabeprazole sodium 20mg gastro-resistant tablet
        ('42357411000001100'),  -- Rabeprazole sodium 10mg gastro-resistant tablet

        -- UK dm+d codes: Ranitidine products
        ('42358011000001105'),  -- Ranitidine 75mg tablet
        ('42357911000001108'),  -- Ranitidine 300mg tablet
        ('42357711000001106'),  -- Ranitidine 150mg tablet
        ('42357611000001102'),  -- Ranitidine 150mg effervescent tablet
        ('42357811000001103'),  -- Ranitidine 300mg effervescent tablet

        -- UK dm+d codes: Famotidine products
        ('42353911000001104'),  -- Famotidine 10mg tablet
        ('42354011000001101'),  -- Famotidine 20mg tablet
        ('42354111000001100'),  -- Famotidine 40mg tablet

        -- UK dm+d codes: Cimetidine products
        ('42351811000001105'),  -- Cimetidine 100mg tablet
        ('42352311000001105'),  -- Cimetidine 800mg tablet
        ('42352211000001102'),  -- Cimetidine 400mg tablet
        ('42351911000001100'),  -- Cimetidine 200mg tablet

        -- UK dm+d codes: Nizatidine products
        ('42355911000001103'),  -- Nizatidine 300mg capsule
        ('42355811000001108')   -- Nizatidine 150mg capsule
    ) AS t(code)
),

patients_with_peptic_ulcer AS (
    -- Find patients with peptic ulcer diagnosis from GP events
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        MIN(ge.EventDate) as earliest_peptic_ulcer_date
    FROM {gp_events_enriched} ge
    WHERE ge.SuppliedCode IN (SELECT code FROM peptic_ulcer_codes)
    GROUP BY ge.FK_Patient_Link_ID
),

patients_with_nsaid AS (
    -- Find patients prescribed NSAIDs after their peptic ulcer diagnosis
    SELECT DISTINCT
        pu.FK_Patient_Link_ID,
        p.medication_start_date as nsaid_start_date,
        p.medication_end_date as nsaid_end_date,
        p.medication_code as nsaid_code,
        p.medication_name as nsaid_name
    FROM patients_with_peptic_ulcer pu
    INNER JOIN {gp_prescriptions} p
        ON pu.FK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE p.medication_code IN (SELECT code FROM nsaid_codes)
        AND p.medication_start_date >= pu.earliest_peptic_ulcer_date
),

patients_with_ulcer_healing_drug AS (
    -- Find patients with ulcer-healing drug prescriptions (PPIs or H2 antagonists)
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        p.medication_start_date as drug_start_date,
        p.medication_end_date as drug_end_date
    FROM {gp_prescriptions} p
    WHERE p.medication_code IN (SELECT code FROM ulcer_healing_drug_codes)
),

nsaid_without_gastroprotection AS (
    -- Find NSAID prescriptions without overlapping ulcer-healing drug co-prescription
    SELECT DISTINCT
        nsaid.FK_Patient_Link_ID,
        nsaid.nsaid_start_date,
        nsaid.nsaid_end_date,
        nsaid.nsaid_name
    FROM patients_with_nsaid nsaid
    WHERE NOT EXISTS (
        -- Check if there's any ulcer-healing drug prescription that overlaps with this NSAID prescription
        SELECT 1
        FROM patients_with_ulcer_healing_drug drug
        WHERE drug.FK_Patient_Link_ID = nsaid.FK_Patient_Link_ID
            -- Drug overlaps with NSAID if:
            -- Drug starts before NSAID ends AND drug ends after NSAID starts
            -- Handle NULL end dates by assuming 90-day duration
            AND drug.drug_start_date <= COALESCE(nsaid.nsaid_end_date, nsaid.nsaid_start_date + INTERVAL '90 days')
            AND COALESCE(drug.drug_end_date, drug.drug_start_date + INTERVAL '90 days') >= nsaid.nsaid_start_date
    )
)

-- Return patient IDs matching this filter with period dates
SELECT DISTINCT
    FK_Patient_Link_ID,
    28 as filter_id,
    nsaid_start_date as start_date,
    nsaid_end_date as end_date
FROM nsaid_without_gastroprotection;
