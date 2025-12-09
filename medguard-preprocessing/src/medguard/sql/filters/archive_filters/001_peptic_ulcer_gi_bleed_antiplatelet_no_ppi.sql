-- Filter 001: Aspirin or clopidogrel prescribed to people with previous peptic ulcer or gastrointestinal bleed without gastroprotection
--
-- This filter identifies patients who:
-- 1. Have a recorded diagnosis of peptic ulcer OR gastrointestinal hemorrhage
-- 2. Have been prescribed aspirin or clopidogrel after their diagnosis
-- 3. Do NOT have a co-prescribed proton pump inhibitor (PPI) during the antiplatelet prescription period
--
-- Design decisions:
-- - Uses GP Events for peptic ulcer and GI bleed diagnoses
-- - Uses GP Prescriptions table for medication prescriptions (consolidated prescription islands)
-- - Co-prescription defined as: PPI prescription with overlapping dates (start/end dates overlap with antiplatelet dates)
-- - Looks for any peptic ulcer or GI bleed diagnosis in patient history
-- - Aspirin includes all formulations (tablets, suppositories, oral solutions)
-- - Clopidogrel includes all formulations (tablets, oral solutions, oral powders)
-- - Prioritizes precision: only flags clear cases of antiplatelet without PPI co-prescription
-- - Risk level: 3 (significant risk of GI complications)

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

gi_bleed_codes AS (
    -- SNOMED codes for gastrointestinal hemorrhage and key descendants
    -- Based on concept_id 74474003 (Gastrointestinal hemorrhage)
    SELECT code FROM (VALUES
        ('74474003'),   -- Gastrointestinal hemorrhage (disorder) [PARENT]
        ('307296008'),  -- Recurrent gastrointestinal bleeding (disorder)
        ('307297004'),  -- Massive gastrointestinal bleed (disorder)
        ('27719009'),   -- Acute gastrointestinal hemorrhage (disorder)
        ('37372002'),   -- Upper gastrointestinal hemorrhage (disorder)
        ('83628005'),   -- Chronic gastrointestinal hemorrhage (disorder)
        ('87763006'),   -- Lower gastrointestinal hemorrhage (disorder)
        ('275551007'),  -- History of gastrointestinal bleed (situation)
        ('293771000119100'), -- History of lower gastrointestinal bleed (situation)

        -- Upper GI bleeding
        ('25349007'),   -- Chronic upper gastrointestinal hemorrhage (disorder)
        ('38938002'),   -- Acute upper gastrointestinal hemorrhage (disorder)
        ('8765009'),    -- Hematemesis (disorder)
        ('15238002'),   -- Esophageal bleeding (disorder)
        ('61401005'),   -- Gastric hemorrhage (disorder)
        ('64121000'),   -- Peptic ulcer with hemorrhage (disorder)
        ('95533003'),   -- Duodenal hemorrhage (disorder)
        ('97801000119102'), -- Gastritis with upper gastrointestinal haemorrhage

        -- Lower GI bleeding
        ('68162000'),   -- Chronic lower gastrointestinal hemorrhage (disorder)
        ('85521005'),   -- Acute lower gastrointestinal hemorrhage (disorder)
        ('95540002'),   -- Hemorrhage of colon (disorder)
        ('12063002'),   -- Rectal hemorrhage (disorder)
        ('51551000'),   -- Bleeding hemorrhoids (disorder)
        ('266464001'),  -- Hemorrhage of rectum and anus (disorder)

        -- Specific bleeding conditions
        ('12274003'),   -- Acute peptic ulcer with hemorrhage (disorder)
        ('2367005'),    -- Acute hemorrhagic gastritis (disorder)
        ('15902003'),   -- Gastric ulcer with hemorrhage (disorder)
        ('17709002'),   -- Bleeding esophageal varices (disorder)
        ('24807004'),   -- Bleeding gastric varices (disorder)
        ('35265002'),   -- Mallory-Weiss syndrome (disorder)
        ('414663001'),  -- Melaena due to gastrointestinal haemorrhage
        ('722886001'),  -- Obscure gastrointestinal haemorrhage
        ('712510007')   -- Intestinal haemorrhage
    ) AS t(code)
),

antiplatelet_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- These codes match actual UK prescription data
    SELECT code FROM (VALUES
        -- Parent/international codes (substance level - for reference)
        ('387458008'),  -- Aspirin [PARENT]
        ('77035009'),   -- Clopidogrel [PARENT]

        -- UK dm+d codes: Aspirin products (THESE MATCH PRESCRIPTIONS!)
        ('42292011000001108'),  -- Aspirin 75mg tablet
        ('42291711000001103'),  -- Aspirin 300mg tablet
        ('42291511000001108'),  -- Aspirin 300mg gastro-resistant tablet
        ('42291911000001101'),  -- Aspirin 75mg gastro-resistant tablet
        ('42291611000001107'),  -- Aspirin 300mg suppository
        ('42291411000001109'),  -- Aspirin 150mg suppository
        ('39695211000001102'),  -- Aspirin 300mg tablet for oral suspension
        ('42291811000001106'),  -- Aspirin 75mg tablet for oral suspension
        ('10064711000001104'),  -- Aspirin 75mg effervescent tablets
        ('8280211000001109'),   -- Aspirin 225mg/5ml oral solution
        ('8280311000001101'),   -- Aspirin 225mg/5ml oral suspension
        ('8280511000001107'),   -- Aspirin 300mg/5ml oral solution
        ('8280611000001106'),   -- Aspirin 300mg/5ml oral suspension
        ('8280711000001102'),   -- Aspirin 50mg/5ml oral solution
        ('8280811000001105'),   -- Aspirin 50mg/5ml oral suspension
        ('12012111000001104'),  -- Aspirin 100mg/5ml oral solution
        ('11712811000001108'),  -- Aspirin 100mg/5ml oral suspension
        ('12012211000001105'),  -- Aspirin 15mg/5ml oral solution
        ('12012311000001102'),  -- Aspirin 15mg/5ml oral suspension
        ('12012511000001108'),  -- Aspirin 25mg/5ml oral solution
        ('12012611000001107'),  -- Aspirin 25mg/5ml oral suspension
        ('12012911000001101'),  -- Aspirin 30mg/5ml oral solution
        ('12013011000001109'),  -- Aspirin 30mg/5ml oral suspension
        ('12013511000001101'),  -- Aspirin 40mg/5ml oral solution
        ('12013711000001106'),  -- Aspirin 40mg/5ml oral suspension
        ('12014011000001106'),  -- Aspirin 75mg/5ml oral solution
        ('12014111000001107'),  -- Aspirin 75mg/5ml oral suspension

        -- UK dm+d codes: Clopidogrel products (THESE MATCH PRESCRIPTIONS!)
        ('39689111000001106'),  -- Clopidogrel 75mg tablet
        ('42293111000001103'),  -- Clopidogrel 300mg tablet
        ('22402511000001104'),  -- Clopidogrel 75mg/5ml oral solution
        ('8426611000001103'),   -- Clopidogrel 75mg/5ml oral suspension
        ('34682711000001102'),  -- Clopidogrel 7mg/ml oral suspension
        ('16072911000001108'),  -- Clopidogrel 25mg/5ml oral suspension
        ('36903411000001109'),  -- Clopidogrel 5mg/5ml oral solution
        ('32392111000001102'),  -- Clopidogrel 6mg/ml oral suspension
        ('18747911000001101'),  -- Clopidogrel 1mg/ml oral suspension
        ('28415011000001107'),  -- Clopidogrel 5mg oral powder sachets
        ('16089411000001101'),  -- Clopidogrel 11mg oral powder sachets
        ('8816311000001106'),   -- Clopidogrel 75mg oral powder sachets
        ('30919611000001101'),  -- Clopidogrel 6mg oral powder sachets
        ('22342711000001109'),  -- Clopidogrel 4mg oral powder sachets
        ('31140711000001100')   -- Clopidogrel 3.5mg oral powder sachets
    ) AS t(code)
),

ppi_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- Proton pump inhibitors for gastroprotection
    SELECT code FROM (VALUES
        -- Parent/international codes (substance level - for reference)
        ('372525000'),  -- Proton pump inhibitor [PARENT]
        ('387137007'),  -- Omeprazole
        ('108466004'),  -- Lansoprazole
        ('396047003'),  -- Pantoprazole
        ('396064002'),  -- Esomeprazole
        ('422225001'),  -- Rabeprazole

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
        ('8670511000001102'),   -- Omeprazole 10mg/5ml oral suspension
        ('8670711000001107'),   -- Omeprazole 20mg/5ml oral suspension
        ('8670811000001104'),   -- Omeprazole 5mg/5ml oral suspension

        -- UK dm+d codes: Lansoprazole products
        ('42354611000001108'),  -- Lansoprazole 30mg gastro-resistant capsule
        ('42354511000001109'),  -- Lansoprazole 15mg gastro-resistant capsule
        ('13821911000001109'),  -- Lansoprazole 5mg/5ml oral suspension
        ('13821811000001104'),  -- Lansoprazole 5mg/5ml oral solution
        ('14742811000001107'),  -- Lansoprazole 10mg oral powder sachets
        ('15533811000001107'),  -- Lansoprazole 10mg/5ml oral suspension
        ('34665111000001107'),  -- Lansoprazole 15mg oral powder sachets

        -- UK dm+d codes: Pantoprazole products
        ('42357111000001105'),  -- Pantoprazole (as sodium sesquihydrate) 40mg gastro-resistant tablet
        ('42357011000001109'),  -- Pantoprazole (as sodium sesquihydrate) 20mg gastro-resistant tablet
        ('42357211000001104'),  -- Pantoprazole (as sodium sesquihydrate) 40mg powder for injection
        ('18520011000001104'),  -- Pantoprazole 20mg/5ml oral suspension
        ('18520111000001103'),  -- Pantoprazole 40mg/5ml oral suspension

        -- UK dm+d codes: Esomeprazole products
        ('42353811000001109'),  -- Esomeprazole 40mg gastro-resistant tablet
        ('42353711000001101'),  -- Esomeprazole 20mg gastro-resistant tablet
        ('17631411000001100'),  -- Esomeprazole 40mg gastro-resistant capsules
        ('17631311000001107'),  -- Esomeprazole 20mg gastro-resistant capsules
        ('16132311000001103'),  -- Esomeprazole 10mg gastro-resistant granules sachets
        ('16074011000001103'),  -- Esomeprazole 40mg/5ml oral suspension

        -- UK dm+d codes: Rabeprazole products
        ('42357511000001101'),  -- Rabeprazole sodium 20mg gastro-resistant tablet
        ('42357411000001100')   -- Rabeprazole sodium 10mg gastro-resistant tablet
    ) AS t(code)
),

patients_with_condition AS (
    -- Find patients with peptic ulcer OR GI bleed diagnosis from GP events
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        MIN(ge.EventDate) as earliest_condition_date
    FROM {gp_events_enriched} ge
    WHERE ge.SuppliedCode IN (
        SELECT code FROM peptic_ulcer_codes
        UNION
        SELECT code FROM gi_bleed_codes
    )
    GROUP BY ge.FK_Patient_Link_ID
),

patients_with_antiplatelet AS (
    -- Find patients prescribed aspirin or clopidogrel after their condition diagnosis
    SELECT DISTINCT
        pc.FK_Patient_Link_ID,
        p.medication_start_date as antiplatelet_start_date,
        p.medication_end_date as antiplatelet_end_date,
        p.medication_code as antiplatelet_code,
        p.medication_name as antiplatelet_name
    FROM patients_with_condition pc
    INNER JOIN {gp_prescriptions} p
        ON pc.FK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE p.medication_code IN (SELECT code FROM antiplatelet_codes)
        AND p.medication_start_date >= pc.earliest_condition_date
),

patients_with_ppi AS (
    -- Find patients with PPI prescriptions
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        p.medication_start_date as ppi_start_date,
        p.medication_end_date as ppi_end_date
    FROM {gp_prescriptions} p
    WHERE p.medication_code IN (SELECT code FROM ppi_codes)
),

antiplatelet_without_ppi AS (
    -- Find antiplatelet prescriptions without overlapping PPI co-prescription
    SELECT DISTINCT
        ap.FK_Patient_Link_ID,
        ap.antiplatelet_start_date,
        ap.antiplatelet_end_date,
        ap.antiplatelet_name
    FROM patients_with_antiplatelet ap
    WHERE NOT EXISTS (
        -- Check if there's any PPI prescription that overlaps with this antiplatelet prescription
        SELECT 1
        FROM patients_with_ppi ppi
        WHERE ppi.FK_Patient_Link_ID = ap.FK_Patient_Link_ID
            -- PPI overlaps with antiplatelet if:
            -- PPI starts before antiplatelet ends AND PPI ends after antiplatelet starts
            AND ppi.ppi_start_date <= ap.antiplatelet_end_date
            AND ppi.ppi_end_date >= ap.antiplatelet_start_date
    )
)

-- Return patient IDs matching this filter with period dates
SELECT DISTINCT
    FK_Patient_Link_ID,
    '001' as filter_id,
    antiplatelet_start_date as start_date,
    antiplatelet_end_date as end_date
FROM antiplatelet_without_ppi;
