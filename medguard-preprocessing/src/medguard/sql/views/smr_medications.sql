-- Track medication changes (started/stopped) around SMR events
CREATE OR REPLACE TABLE {smr_medications_table} AS
WITH smr_events AS (
    SELECT DISTINCT
        FK_Patient_Link_ID,
        EventDate as smr_date
    FROM {gp_events_view} gp
    INNER JOIN SMRCodes c ON c.code = gp.SuppliedCode
),

-- Medications that were active at all in 3 months prior to SMR
meds_before_smr AS (
    SELECT DISTINCT
        s.FK_Patient_Link_ID,
        s.smr_date,
        p.medication_code,
        p.medication_name
    FROM smr_events s
    INNER JOIN {gp_prescriptions} p
        ON s.FK_Patient_Link_ID = p.FK_Patient_Link_ID
        AND p.medication_start_date < s.smr_date     -- started before the SMR
        AND p.medication_end_date > s.smr_date - INTERVAL '3 MONTHS'  -- ended within 3 months
        AND is_repeat_medication = TRUE
),

-- Medications that were active after the SMR
meds_after_smr AS (
    SELECT DISTINCT
        s.FK_Patient_Link_ID,
        s.smr_date,
        p.medication_code,
        p.medication_name
    FROM smr_events s
    INNER JOIN {gp_prescriptions} p
        ON s.FK_Patient_Link_ID = p.FK_Patient_Link_ID
        AND p.medication_start_date < s.smr_date + INTERVAL '3 MONTHS'
        AND p.medication_end_date > s.smr_date
        AND is_repeat_medication = TRUE
),

-- Identify STOPPED medications (active before, inactive after)
stopped_medications AS (
    SELECT
        b.FK_Patient_Link_ID,
        b.smr_date,
        b.medication_code,
        b.medication_name,
        'stopped' as change_type
    FROM meds_before_smr b
    LEFT JOIN meds_after_smr a
        ON b.FK_Patient_Link_ID = a.FK_Patient_Link_ID
        AND b.smr_date = a.smr_date
        AND b.medication_code = a.medication_code
    WHERE a.medication_code IS NULL
),

-- Identify STARTED medications (inactive before, active after)
started_medications AS (
    SELECT 
        a.FK_Patient_Link_ID,
        a.smr_date,
        a.medication_code,
        a.medication_name,
        'started' as change_type
    FROM meds_after_smr a
    LEFT JOIN meds_before_smr b
        ON a.FK_Patient_Link_ID = b.FK_Patient_Link_ID
        AND a.smr_date = b.smr_date
        AND a.medication_code = b.medication_code
    WHERE b.medication_code IS NULL
),

medication_changes AS (
    SELECT
        FK_Patient_Link_ID,
        smr_date,
        medication_code,
        medication_name,
        change_type
    FROM stopped_medications

    UNION ALL

    SELECT
        FK_Patient_Link_ID,
        smr_date,
        medication_code,
        medication_name,
        change_type
    FROM started_medications
)

SELECT * FROM medication_changes 
ORDER BY FK_Patient_Link_ID, smr_date DESC, medication_code DESC