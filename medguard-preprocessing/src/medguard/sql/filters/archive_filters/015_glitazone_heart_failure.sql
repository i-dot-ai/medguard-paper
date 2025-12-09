-- Filter 015: Glitazone prescribed to patient with heart failure
-- Description: Prescription of a glitazone (pioglitazone or rosiglitazone) to a patient with heart failure
-- Glitazones can cause fluid retention and worsen heart failure, making them contraindicated in HF patients
--
-- This filter identifies patients who:
-- 1. Have a recorded diagnosis of heart failure
-- 2. Have been prescribed a glitazone (pioglitazone or rosiglitazone) after their heart failure diagnosis

WITH glitazone_medication_codes AS (
    SELECT code FROM (VALUES
        -- Pioglitazone tablets (15mg, 30mg, 45mg - various manufacturers)
        ('42086211000001105'), ('42086311000001102'), ('42086411000001109'),
        ('1126211000001109'), ('1011011000001108'), ('5199211000001106'),
        ('20319611000001106'), ('20320211000001108'), ('20320611000001105'),
        ('30077211000001109'), ('30112111000001103'), ('30112311000001101'),
        ('39187811000001106'), ('39187611000001107'), ('39188011000001104'),
        ('19476211000001103'), ('19476611000001101'), ('19476411000001104'),
        ('23487811000001109'), ('23487611000001105'), ('23487411000001107'),
        ('20357411000001107'), ('20357611000001105'), ('20357811000001109'),
        ('21763311000001107'), ('21764211000001101'), ('21764511000001103'),
        ('21848111000001107'), ('21848311000001109'), ('21848511000001103'),
        ('24134911000001102'), ('24135111000001101'), ('24137211000001104'),
        ('29985811000001104'), ('29986011000001101'), ('29986211000001106'),
        ('22949011000001105'), ('22949511000001102'), ('22949311000001108'),
        ('20917311000001102'), ('20917111000001104'), ('20916911000001104'),
        ('33598911000001107'), ('33598711000001105'), ('33599111000001102'),
        ('19469211000001102'), ('19469411000001103'), ('19469611000001100'),
        ('20319711000001102'), ('20320311000001100'), ('20320811000001109'),
        ('30077311000001101'), ('30112211000001109'), ('30112411000001108'),
        ('30857011000001100'), ('30857211000001105'), ('30857411000001109'),
        ('32492811000001102'), ('32493011000001104'), ('32493211000001109'),
        ('36856611000001103'), ('36857111000001109'), ('36857411000001104'),
        ('39188111000001103'), ('39187911000001101'), ('39187711000001103'),
        ('19361311000001103'), ('19361511000001109'), ('19473511000001108'),
        ('21848211000001101'), ('21848411000001102'), ('21848711000001108'),
        ('24135011000001102'), ('24137311000001107'), ('24137711000001106'),
        ('29985911000001109'), ('29986111000001100'), ('29986311000001103'),
        ('20917411000001109'), ('20917011000001100'), ('20917211000001105'),
        ('33598811000001102'), ('33599211000001108'), ('33599011000001103'),
        ('19469311000001105'), ('19469511000001104'), ('19469711000001109'),
        ('19592911000001108'), ('19593111000001104'), ('19593311000001102'),
        ('30857111000001104'), ('30857311000001102'), ('30857511000001108'),
        ('36856811000001104'), ('36857211000001103'), ('36857511000001100'),
        ('19473611000001107'), ('19361411000001105'),
        ('19593011000001100'), ('19593211000001105'), ('19593411000001109'),
        ('19476711000001105'), ('19476511000001100'), ('19476311000001106'),
        ('23487711000001101'), ('23488111000001101'), ('23487511000001106'),
        ('20357511000001106'), ('20357711000001101'), ('20357911000001104'),
        ('21763511000001101'), ('21764411000001102'), ('21764611000001104'),
        ('22949411000001101'), ('22949711000001107'), ('22949211000001100'),
        ('32492911000001107'), ('32493111000001103'), ('32493311000001101'),
        ('19361611000001108'),

        -- Pioglitazone oral suspensions
        ('16036811000001104'), ('18595311000001103'), ('13440011000001109'),
        ('13435011000001104'), ('13434911000001104'), ('16007611000001109'),
        ('16007511000001105'), ('18567011000001105'), ('18566811000001101'),
        ('13435111000001103'), ('16007711000001100'), ('18567111000001106'),

        -- Pioglitazone/Metformin combination tablets
        ('42086111000001104'), ('10922211000001100'),
        ('37775311000001103'), ('40327411000001109'),
        ('35653211000001103'), ('37775411000001105'),
        ('36468511000001101'), ('36832811000001104'),
        ('35672911000001103'), ('36468611000001102'),
        ('36832911000001109'), ('35673011000001106'),
        ('35653311000001106'), ('40327511000001108'),

        -- Rosiglitazone tablets (4mg, 8mg)
        ('42089111000001107'), ('42089211000001101'),
        ('1193711000001103'), ('1135711000001107'),
        ('1237011000001100'), ('10464411000001101'),

        -- Rosiglitazone/Metformin combination tablets
        ('42088811000001107'), ('42089011000001106'),
        ('42088911000001102'), ('42088711000001104'),
        ('8174511000001105'), ('8176211000001102'),
        ('5303411000001101'), ('17533311000001102'),
        ('5302711000001104')
    ) AS t(code)
),

heart_failure_codes AS (
    SELECT code FROM (VALUES
        -- Heart failure diagnoses
        ('84114007'),   -- Heart failure (disorder)
        ('42343007'),   -- Congestive heart failure (disorder)
        ('48447003'),   -- Chronic heart failure (disorder)
        ('56675007'),   -- Acute heart failure (disorder)
        ('85232009'),   -- Left heart failure (disorder)
        ('367363000'),  -- Right ventricular failure (disorder)
        ('44313006'),   -- Right heart failure secondary to left heart failure (disorder)
        ('23341000119109'), -- Congestive heart failure with right heart failure (disorder)
        ('46113002'),   -- Hypertensive heart failure (disorder)
        ('314206003'),  -- Refractory heart failure (disorder)
        ('418304008'),  -- Diastolic heart failure
        ('417996009'),  -- Systolic heart failure
        ('462172006'),  -- Fetal heart failure
        ('898208007'),  -- Heart failure due to thyrotoxicosis
        ('10091002'),   -- High output heart failure (disorder)
        ('10633002'),   -- Acute congestive heart failure (disorder)
        ('25544003'),   -- Low output heart failure (disorder)
        ('82523003'),   -- Congestive rheumatic heart failure (disorder)
        ('88805009'),   -- Chronic congestive heart failure (disorder)
        ('92506005'),   -- Biventricular congestive heart failure (disorder)
        ('364006'),     -- Acute left-sided heart failure (disorder)
        ('424404003'),  -- Decompensated chronic heart failure
        ('161505003'),  -- History of heart failure (situation)
        ('395105005')   -- Heart failure confirmed (situation)
    ) AS t(code)
),

heart_failure_diagnoses AS (
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        ge.EventDate AS diagnosis_date
    FROM {gp_events_enriched} ge
    INNER JOIN heart_failure_codes hfc ON CAST(ge.SuppliedCode AS VARCHAR) = hfc.code
    WHERE ge.EventDate IS NOT NULL
),

glitazone_prescriptions AS (
    SELECT DISTINCT
        gp.FK_Patient_Link_ID,
        gp.medication_start_date,
        gp.medication_end_date,
        gp.medication_name
    FROM {gp_prescriptions} gp
    INNER JOIN glitazone_medication_codes gmc ON gp.medication_code = gmc.code
    WHERE gp.medication_start_date IS NOT NULL
),

contraindicated_prescriptions AS (
    SELECT DISTINCT
        gp.FK_Patient_Link_ID,
        gp.medication_start_date,
        gp.medication_end_date,
        gp.medication_name,
        hfd.diagnosis_date
    FROM glitazone_prescriptions gp
    INNER JOIN heart_failure_diagnoses hfd
        ON gp.FK_Patient_Link_ID = hfd.FK_Patient_Link_ID
    -- Prescription occurred after heart failure diagnosis (or same day)
    WHERE gp.medication_start_date >= hfd.diagnosis_date
)

SELECT
    FK_Patient_Link_ID,
    '015' AS filter_id,
    medication_start_date AS start_date,
    medication_end_date AS end_date
FROM contraindicated_prescriptions
ORDER BY FK_Patient_Link_ID, medication_start_date;
