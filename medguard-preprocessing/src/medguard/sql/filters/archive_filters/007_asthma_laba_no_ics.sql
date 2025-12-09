-- Filter 007: Prescription of a long-acting beta-2 agonist inhaler to a patient with asthma who is not also prescribed an inhaled corticosteroid
--
-- This filter identifies patients who:
-- 1. Have a recorded diagnosis of asthma (any type)
-- 2. Have been prescribed a long-acting beta-2 agonist (LABA) inhaler
-- 3. Do NOT have an overlapping prescription for an inhaled corticosteroid (ICS)
--
-- Design decisions:
-- - Uses GP Events for asthma diagnoses
-- - Uses GP Prescriptions table for medication prescriptions (consolidated prescription islands)
-- - LABA monotherapy only (excludes LABA+ICS combination inhalers)
-- - ICS includes: beclometasone, budesonide, fluticasone, mometasone inhalers
-- - Clinical rationale: LABAs should not be used as monotherapy in asthma
-- - LABAs without ICS can increase risk of asthma-related death
-- - LABA monotherapy may mask worsening asthma while not treating underlying inflammation
-- - NICE/BTS guidelines: LABA should always be used WITH ICS in asthma (unlike COPD)
-- - Overlap checking: ICS must overlap with LABA prescription period
-- - Risk level: 3 (significant risk - increased asthma mortality without ICS)

WITH asthma_codes AS (
    -- SNOMED codes for asthma and all descendants
    SELECT code FROM (VALUES
        ('195967001'),  -- Asthma (disorder) [PARENT]
        ('225057002'),  -- Brittle asthma (disorder)
        ('233679003'),  -- Late onset asthma (disorder)
        ('266361008'),  -- Non-allergic asthma (disorder)
        ('281239006'),  -- Acute asthma
        ('55570000'),   -- Asthma without status asthmaticus (disorder)
        ('93432008'),   -- Drug-induced asthma (disorder)
        ('195977004'),  -- Mixed asthma (disorder)
        ('233678006'),  -- Childhood asthma (disorder)
        ('405944004'),  -- Asthmatic bronchitis
        ('409663006'),  -- Cough variant asthma
        ('389145006'),  -- Allergic asthma
        ('370218001'),  -- Mild asthma (disorder)
        ('370219009'),  -- Moderate asthma (disorder)
        ('370220003'),  -- Occasional asthma (disorder)
        ('370221004'),  -- Severe asthma (disorder)
        ('92807009'),   -- Chemical-induced asthma (disorder)
        ('427603009'),  -- Intermittent asthma
        ('445427006'),  -- Seasonal asthma
        ('57607007'),   -- Occupational asthma (disorder)
        ('401000119107'), -- Asthma with irreversible airway obstruction
        ('707444001'),  -- Uncomplicated asthma (disorder)
        ('10692761000119107'), -- Asthma-COPD overlap syndrome
        ('2360001000004109'), -- Steroid dependent asthma (disorder)
        ('72301000119103'), -- Asthma in pregnancy
        ('233691007'),  -- Asthmatic pulmonary eosinophilia (disorder)
        ('1290026000'),  -- Uncontrolled asthma
        ('12428000'),   -- Intrinsic asthma without status asthmaticus
        ('63088003'),   -- Allergic asthma without status asthmaticus
        ('195949008'),  -- Chronic asthmatic bronchitis (disorder)
        ('424643009'),  -- IgE-mediated allergic asthma
        ('423889005'),  -- Non-IgE mediated allergic asthma
        ('427679007'),  -- Mild intermittent asthma
        ('426979002'),  -- Mild persistent asthma
        ('427295004'),  -- Moderate persistent asthma
        ('426656000')   -- Severe persistent asthma
    ) AS t(code)
),

laba_monotherapy_codes AS (
    -- IMPORTANT: LABA monotherapy only (excludes LABA+ICS combination inhalers)
    -- UK dm+d codes for long-acting beta-2 agonists
    -- LABAs include: salmeterol, formoterol, vilanterol, indacaterol, olodaterol
    SELECT code FROM (VALUES
        -- Parent/international codes (substance level - for reference)
        ('372515005'),  -- Salmeterol [PARENT]
        ('414289007'),  -- Formoterol [PARENT]

        -- UK dm+d codes: Salmeterol monotherapy inhalers
        -- 25 microgram/dose pressurized inhalers
        ('10075611000001101'),  -- Salmeterol 25micrograms/dose inhaler CFC free
        ('1048111000001108'),   -- Salmeterol 25micrograms/dose inhaler 120 dose
        ('4840011000001103'),   -- Salmeterol 25micrograms/dose inhaler 60 dose
        ('5315611000001101'),   -- Salmeterol 25micrograms/dose inhaler (Dowelhurst Ltd)
        ('5275011000001108'),   -- Salmeterol 25micrograms/dose inhaler (Waymade Healthcare Plc)
        ('5315811000001102'),   -- Salmeterol 25micrograms/dose inhaler (Dowelhurst Ltd) 120 dose
        ('10072811000001109'),  -- Salmeterol 25micrograms/dose inhaler CFC free 120 dose
        ('5275111000001109'),   -- Salmeterol 25micrograms/dose inhaler (Waymade Healthcare Plc) 120 dose

        -- 50 microgram/dose dry powder inhalers (monotherapy)
        ('3379911000001105'),   -- Salmeterol 50micrograms/dose dry powder inhaler 60 dose

        -- UK dm+d codes: Formoterol monotherapy inhalers
        -- 12 microgram/dose inhalers
        ('9652711000001107'),   -- Formoterol 12micrograms/dose inhaler CFC free
        ('3244611000001109'),   -- Formoterol 12micrograms/dose dry powder inhaler 60 dose
        ('9628611000001102'),   -- Formoterol 12micrograms/dose inhaler CFC free 100 dose
        ('11176311000001104'),  -- Formoterol 12micrograms/dose dry powder inhaler 120 dose
        ('11176411000001106'),  -- Formoterol Easyhaler 12micrograms/dose dry powder inhaler (Orion Pharma (UK) Ltd)
        ('11176511000001105'),  -- Formoterol Easyhaler 12micrograms/dose dry powder inhaler (Orion Pharma (UK) Ltd) 120 dose

        -- 6 microgram/dose inhalers (monotherapy only)
        ('3243011000001104')    -- Formoterol 6micrograms/dose dry powder inhaler 60 dose

        -- Note: Excluded LABA+ICS combination inhalers:
        -- - Fluticasone + Salmeterol (Seretide, AirFluSal, etc.)
        -- - Budesonide + Formoterol (Symbicort, DuoResp, etc.)
        -- - Beclometasone + Formoterol (Fostair, Luforbec, etc.)
        -- - Fluticasone furoate + Vilanterol (Relvar)
        -- - Mometasone + Indacaterol
        -- These are appropriate for asthma as they contain ICS

        -- Note: Vilanterol, indacaterol, olodaterol monotherapy inhalers
        -- were not found in UK dm+d - these are primarily licensed for COPD
        -- and typically only available in combination products
    ) AS t(code)
),

ics_codes AS (
    -- IMPORTANT: Inhaled corticosteroid (ICS) codes
    -- UK dm+d codes for ICS inhalers (monotherapy)
    -- ICS include: beclometasone, budesonide, fluticasone, mometasone
    SELECT code FROM (VALUES
        -- UK dm+d codes: Beclometasone inhalers (various strengths)
        ('42292311000001106'),  -- Beclometasone 100micrograms/dose inhaler
        ('3177811000001100'),   -- Beclometasone 100micrograms/dose inhaler 200 dose
        ('4842111000001103'),   -- Beclometasone 100micrograms/dose inhaler 80 dose
        ('35907811000001102'),  -- Beclometasone 100micrograms/dose breath actuated inhaler
        ('35908011000001109'),  -- Beclometasone 100micrograms/dose dry powder inhaler
        ('35908111000001105'),  -- Beclometasone 100micrograms/dose inhaler CFC free
        ('3112111000001100'),   -- Beclometasone 100micrograms/dose dry powder inhaler 100 dose
        ('3112211000001106'),   -- Beclometasone 100micrograms/dose dry powder inhaler 200 dose
        ('3175511000001107'),   -- Beclometasone 100micrograms/dose inhaler CFC free 200 dose
        ('3181311000001109'),   -- Beclometasone 100micrograms/dose breath actuated inhaler 200 dose
        ('35907911000001107'),  -- Beclometasone 100micrograms/dose breath actuated inhaler CFC free
        ('3177611000001104'),   -- Beclometasone 100micrograms/dose breath actuated inhaler CFC free 200 dose

        -- UK dm+d codes: Budesonide inhalers (various strengths)
        ('35912511000001101'),  -- Budesonide 200micrograms/dose inhaler
        ('4864911000001104'),   -- Budesonide 200micrograms/dose inhaler with spacer
        ('2923911000001105'),   -- Budesonide 200micrograms/dose inhaler 200 dose
        ('11361011000001105'),  -- Budesonide 200micrograms/dose inhaler 100 dose
        ('15374611000001106'),  -- Budesonide 200micrograms/dose inhaler CFC free
        ('35912411000001100'),  -- Budesonide 200micrograms/dose dry powder inhaler
        ('9117811000001107'),   -- Budesonide 200micrograms/dose dry powder inhalation cartridge
        ('3112311000001103'),   -- Budesonide 200micrograms/dose dry powder inhaler 100 dose
        ('4860711000001107'),   -- Budesonide 200micrograms/dose inhaler with spacer 200 dose
        ('10074711000001106'),  -- Budesonide 200micrograms/dose dry powder inhaler 200 dose
        ('15358311000001109'),  -- Budesonide 200micrograms/dose inhaler CFC free 120 dose
        ('8024611000001102'),   -- Budesonide 200micrograms/dose dry powder inhalation cartridge with device
        ('9111711000001108'),   -- Budesonide 200micrograms/dose dry powder inhalation cartridge 100 dose
        ('8024711000001106'),   -- Budesonide 200micrograms/dose dry powder inhalation cartridge with device 100 dose

        -- UK dm+d codes: Fluticasone inhalers (various strengths)
        ('971711000001105'),    -- Fluticasone 250micrograms/dose inhaler CFC free 120 dose
        ('1245411000001104'),   -- Fluticasone 250micrograms/dose inhaler CFC free 60 dose

        -- UK dm+d codes: Mometasone inhalers
        ('4045111000001106'),   -- Mometasone 200micrograms/dose dry powder inhaler 30 dose
        ('4045211000001100')    -- Mometasone 200micrograms/dose dry powder inhaler 60 dose

        -- Note: This list includes common ICS monotherapy formulations
        -- Additional strengths and formulations exist but key products are covered
    ) AS t(code)
),

patients_with_asthma AS (
    -- Find patients with asthma diagnosis from GP events
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        MIN(ge.EventDate) as earliest_asthma_date
    FROM {gp_events_enriched} ge
    WHERE ge.SuppliedCode IN (SELECT code FROM asthma_codes)
    GROUP BY ge.FK_Patient_Link_ID
),

patients_with_laba AS (
    -- Find patients with asthma prescribed LABA monotherapy
    SELECT DISTINCT
        pa.FK_Patient_Link_ID,
        p.medication_start_date as laba_start_date,
        p.medication_end_date as laba_end_date,
        p.medication_code as laba_code,
        p.medication_name as laba_name
    FROM patients_with_asthma pa
    INNER JOIN {gp_prescriptions} p
        ON pa.FK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE p.medication_code IN (SELECT code FROM laba_monotherapy_codes)
        AND p.medication_start_date >= pa.earliest_asthma_date
),

patients_with_ics AS (
    -- Find all ICS prescriptions for patients with LABA
    SELECT DISTINCT
        pl.FK_Patient_Link_ID,
        pl.laba_start_date,
        pl.laba_end_date,
        pl.laba_code,
        pl.laba_name,
        p.medication_start_date as ics_start_date,
        p.medication_end_date as ics_end_date
    FROM patients_with_laba pl
    INNER JOIN {gp_prescriptions} p
        ON pl.FK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE p.medication_code IN (SELECT code FROM ics_codes)
        -- Check for overlapping ICS prescription during LABA period
        AND p.medication_start_date <= pl.laba_end_date
        AND p.medication_end_date >= pl.laba_start_date
),

patients_laba_without_ics AS (
    -- Find patients with LABA but NO overlapping ICS prescription
    SELECT
        pl.FK_Patient_Link_ID,
        pl.laba_start_date,
        pl.laba_end_date,
        pl.laba_code,
        pl.laba_name
    FROM patients_with_laba pl
    LEFT JOIN patients_with_ics pi
        ON pl.FK_Patient_Link_ID = pi.FK_Patient_Link_ID
        AND pl.laba_start_date = pi.laba_start_date
        AND pl.laba_end_date = pi.laba_end_date
        AND pl.laba_code = pi.laba_code
    WHERE pi.FK_Patient_Link_ID IS NULL  -- No overlapping ICS found
)

-- Return patient IDs matching this filter with period dates
SELECT DISTINCT
    FK_Patient_Link_ID,
    '007' as filter_id,
    laba_start_date as start_date,
    laba_end_date as end_date
FROM patients_laba_without_ics;
