-- Filter 017: Oral prednisolone prescribed at a dose ≥7.5mg daily for more than 3 months to the over 65s without co-prescription of osteoporosis-preventing treatments
-- Description: Long-term corticosteroid use at therapeutic doses increases fracture risk and requires bone protection
--
-- This filter identifies patients who:
-- 1. Are aged >65 years
-- 2. Receive oral prednisolone prescriptions for >90 days duration
-- 3. Are prescribed doses typically ≥7.5mg daily (based on tablet strength and duration)
-- 4. Do NOT have co-prescribed osteoporosis prevention treatments
--
-- Design decisions:
-- - Focus on tablet formulations only (oral route most relevant for chronic use)
-- - Duration calculated from prescription dates (>90 days = >3 months)
-- - Include tablets ≥5mg strength (likely therapeutic doses)
-- - Check for osteoporosis prevention during or up to 30 days before prednisolone
-- - Bone protection includes: bisphosphonates, denosumab, raloxifene, strontium, teriparatide

WITH prednisolone_tablet_codes AS (
    SELECT code FROM (VALUES
        -- Prednisolone 5mg tablets (common starting dose for inflammatory conditions)
        ('42087311000001104'), ('1085511000001104'), ('13245511000001105'),
        ('30115011000001109'), ('40021511000001101'), ('85511000001101'),
        ('43928811000001103'), ('44944011000001100'), ('772111000001107'),
        ('10410111000001103'), ('110811000001100'), ('940311000001100'),
        ('9807911000001105'), ('14786711000001109'), ('21851411000001106'),
        ('32808311000001101'), ('350611000001104'), ('86711000001103'),
        ('30859111000001105'), ('18285211000001104'), ('38721711000001107'),

        -- Prednisolone 10mg tablets
        ('28808411000001103'), ('32772011000001109'), ('39169811000001100'),
        ('32771211000001106'), ('32776311000001106'),

        -- Prednisolone 20mg tablets
        ('28808711000001109'), ('32773111000001104'), ('39888311000001108'),
        ('32773211000001105'), ('32776511000001100'),

        -- Prednisolone 25mg tablets
        ('42087011000001102'), ('1009611000001103'), ('37778711000001106'),
        ('39180111000001100'), ('30991311000001108'), ('313911000001107'),
        ('716111000001103'), ('37131011000001108'),

        -- Prednisolone 30mg tablets
        ('32781411000001102'), ('32774311000001100'), ('39173511000001107'),
        ('32774411000001107'), ('32776711000001105'),

        -- Prednisolone 50mg tablets (definitely high dose)
        ('42087111000001101'), ('4752511000001108'), ('4752811000001106')
    ) AS t(code)
),

-- Osteoporosis prevention medication codes
osteoporosis_prevention_codes AS (
    SELECT code FROM (VALUES
        -- Alendronic acid tablets (all strengths)
        ('1273311000001106'), ('1016611000001108'), ('3145611000001107'),
        ('9526611000001107'), ('36508211000001106'), ('35134211000001102'),
        ('5462511000001103'), ('13104211000001104'), ('19701111000001102'),
        ('19700911000001106'), ('24111211000001100'), ('36925711000001107'),
        ('18066611000001102'), ('38771111000001105'), ('38771311000001107'),
        ('40849811000001104'), ('18455711000001102'), ('18455911000001100'),
        ('9188811000001108'), ('9251711000001102'), ('9299611000001102'),
        ('9452511000001100'), ('9830711000001104'), ('10284811000001101'),
        ('10285011000001106'), ('10447611000001104'), ('9836811000001109'),
        ('10688611000001108'), ('13441411000001109'), ('14111911000001105'),
        ('13764011000001102'), ('15060811000001107'), ('15060411000001105'),
        ('17961911000001104'), ('17963711000001100'), ('21756211000001101'),
        ('10435111000001104'), ('37028611000001103'), ('13719811000001106'),
        ('9990311000001102'), ('9990111000001104'), ('9764011000001100'),
        ('9208911000001102'), ('9554311000001109'), ('9554111000001107'),

        -- Risedronate sodium tablets
        ('1047411000001102'), ('3778411000001106'), ('4028111000001103'),
        ('10910011000001102'), ('10785211000001106'), ('20889411000001109'),
        ('30090111000001105'), ('30090311000001107'), ('30090511000001101'),
        ('37911811000001106'), ('37912211000001103'), ('37912011000001108'),
        ('39223511000001109'), ('39227411000001103'), ('39223711000001104'),
        ('18308311000001108'), ('18358911000001102'), ('18359411000001102'),
        ('18359911000001105'), ('18597911000001107'), ('18741911000001109'),
        ('18742111000001101'), ('18742311000001104'), ('19215711000001107'),
        ('20536311000001101'), ('21886911000001103'), ('21887111000001103'),
        ('21887311000001101'), ('23666911000001101'), ('23667111000001101'),
        ('23667311000001104'), ('31321011000001100'), ('31322411000001104'),
        ('18552311000001103'), ('18354811000001104'), ('22350911000001109'),
        ('33614811000001104'), ('19830011000001100'),

        -- Ibandronic acid tablets
        ('9553111000001105'), ('7540011000001105'), ('9544811000001102'),
        ('9563811000001109'), ('20289811000001101'), ('24172711000001107'),
        ('24173111000001100'), ('36626611000001109'), ('40978211000001101'),
        ('38968511000001108'), ('38968211000001105'), ('40858011000001103'),
        ('40901811000001100'), ('20947711000001105'), ('19295711000001108'),
        ('20596011000001106'), ('20946211000001100'), ('22045211000001108'),
        ('22045411000001107'), ('22464211000001105'), ('29875211000001102'),
        ('29875611000001100'), ('34105011000001109'), ('35922211000001107'),
        ('35922511000001105'), ('22086511000001105'), ('19275511000001106'),

        -- Zoledronic acid infusions
        ('24408911000001102'), ('28991011000001109'), ('24055311000001109'),
        ('7335511000001105'), ('23661711000001109'),

        -- Denosumab injections
        ('19448111000001109'), ('17313111000001106'), ('19376011000001101'),
        ('42694311000001101'), ('17301711000001109'),

        -- Raloxifene tablets
        ('1142811000001107'), ('1238711000001102'), ('10485311000001105'),
        ('24110811000001107'), ('30086311000001109'), ('33971011000001100'),
        ('38744511000001103'), ('39205211000001101'), ('24559611000001104'),
        ('14617011000001102'), ('22109311000001101'), ('22517711000001102'),
        ('34444711000001101'), ('33612911000001100'),

        -- Strontium ranelate sachets
        ('8166211000001105'), ('36511011000001109'), ('40264211000001101'),

        -- Teriparatide injections
        ('37753511000001108'), ('35916511000001100'), ('37753611000001107'),
        ('5254011000001106'), ('5253911000001108'), ('38774711000001109'),
        ('42892411000001108'), ('19606611000001109'), ('40670211000001103'),
        ('40991211000001104'), ('44936211000001101')
    ) AS t(code)
),

-- Elderly patients (>65 years old at current date)
elderly_patients AS (
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        p.Dob
    FROM {patient_view} p
    WHERE p.Dob IS NOT NULL
        AND DATE_DIFF('year', p.Dob, CURRENT_DATE) > 65
),

-- Long-duration prednisolone prescriptions in elderly patients
long_prednisolone_elderly AS (
    SELECT DISTINCT
        ep.FK_Patient_Link_ID,
        pr.medication_start_date,
        pr.medication_end_date,
        pr.medication_name,
        DATE_DIFF('year', ep.Dob, pr.medication_start_date) as age_at_prescription
    FROM elderly_patients ep
    INNER JOIN {gp_prescriptions} pr
        ON ep.FK_Patient_Link_ID = pr.FK_Patient_Link_ID
    INNER JOIN prednisolone_tablet_codes ptc
        ON pr.medication_code = ptc.code
    WHERE pr.medication_start_date IS NOT NULL
        -- Patient was over 65 at time of prescription
        AND DATE_DIFF('year', ep.Dob, pr.medication_start_date) > 65
        -- Duration more than 90 days (3 months)
        AND (
            (pr.medication_end_date IS NOT NULL
             AND DATE_DIFF('day', pr.medication_start_date, pr.medication_end_date) > 90)
        )
),

-- Osteoporosis prevention prescriptions
osteoporosis_prevention AS (
    SELECT DISTINCT
        pr.FK_Patient_Link_ID,
        pr.medication_start_date as prevention_start_date,
        pr.medication_end_date as prevention_end_date
    FROM {gp_prescriptions} pr
    INNER JOIN osteoporosis_prevention_codes opc
        ON pr.medication_code = opc.code
    WHERE pr.medication_start_date IS NOT NULL
),

-- Prednisolone without bone protection
prednisolone_without_protection AS (
    SELECT DISTINCT
        lpe.FK_Patient_Link_ID,
        lpe.medication_start_date,
        lpe.medication_end_date,
        lpe.medication_name
    FROM long_prednisolone_elderly lpe
    WHERE NOT EXISTS (
        SELECT 1
        FROM osteoporosis_prevention op
        WHERE op.FK_Patient_Link_ID = lpe.FK_Patient_Link_ID
            -- Prevention overlaps with or starts before/during prednisolone
            -- Allow prescriptions that start up to 30 days before prednisolone
            AND op.prevention_start_date >= (lpe.medication_start_date - INTERVAL '30 days')
            AND op.prevention_start_date <= COALESCE(lpe.medication_end_date, lpe.medication_start_date + INTERVAL '120 days')
    )
)

SELECT DISTINCT
    FK_Patient_Link_ID,
    '017' as filter_id,
    medication_start_date as start_date,
    medication_end_date as end_date
FROM prednisolone_without_protection
ORDER BY FK_Patient_Link_ID, medication_start_date;
