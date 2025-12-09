-- Compute stratification features for all patients at a specific sample_date
-- Used for matched sampling of negative control patients
--
-- Parameters:
--   - sample_date: The reference date for calculating age and active medications
--
-- Returns: FK_Patient_Link_ID, age, gender, condition_count, prescription_count,
--          age_bin, condition_bin, prescription_bin, stratum_key

WITH patient_demographics AS (
    -- Get basic demographics calculated at sample_date
    SELECT
        PK_Patient_Link_ID as FK_Patient_Link_ID,
        Dob,
        Sex,
        DATE_DIFF('year', Dob, DATE '{sample_date}') as age
    FROM {patient_link_view} pl
    LEFT JOIN {patient_view} p ON pl.PK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
        AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
        {deceased_filter}
),

patient_conditions AS (
    -- Count distinct GP events per patient from 2020 up to sample_date
    SELECT
        FK_Patient_Link_ID,
        COUNT(DISTINCT PK_GP_Events_ID) as condition_count
    FROM {gp_events_enriched}
    WHERE (Deleted = 'N' OR Deleted IS NULL)
        AND EventDate IS NOT NULL
        AND EventDate >= '2020-01-01'
        AND EventDate <= DATE '{sample_date}'
    GROUP BY FK_Patient_Link_ID
),

patient_prescriptions AS (
    -- Count distinct active medication codes at sample_date
    -- Active = started before/at sample_date AND (not ended OR ended after sample_date)
    SELECT
        FK_Patient_Link_ID,
        COUNT(DISTINCT medication_code) as prescription_count
    FROM {gp_prescriptions}
    WHERE medication_start_date IS NOT NULL
        AND medication_start_date <= DATE '{sample_date}'
        AND (medication_end_date IS NULL OR medication_end_date >= DATE '{sample_date}')
    GROUP BY FK_Patient_Link_ID
)

SELECT
    pd.FK_Patient_Link_ID,
    pd.age,
    pd.Sex as gender,
    COALESCE(pc.condition_count, 0) as condition_count,
    COALESCE(pp.prescription_count, 0) as prescription_count,

    -- Age bins: <40, 40-60, 60-75, >75
    CASE
        WHEN pd.age IS NULL THEN 'unknown'
        WHEN pd.age < 40 THEN '<40'
        WHEN pd.age >= 40 AND pd.age < 60 THEN '40-60'
        WHEN pd.age >= 60 AND pd.age < 75 THEN '60-75'
        ELSE '>75'
    END as age_bin,

    -- Condition bins: 0-10, 11-25, 26-50, >50
    CASE
        WHEN COALESCE(pc.condition_count, 0) <= 10 THEN '0-10'
        WHEN COALESCE(pc.condition_count, 0) <= 25 THEN '11-25'
        WHEN COALESCE(pc.condition_count, 0) <= 50 THEN '26-50'
        ELSE '>50'
    END as condition_bin,

    -- Prescription bins: 0-5, 6-12, 13-20, >20
    CASE
        WHEN COALESCE(pp.prescription_count, 0) <= 5 THEN '0-5'
        WHEN COALESCE(pp.prescription_count, 0) <= 12 THEN '6-12'
        WHEN COALESCE(pp.prescription_count, 0) <= 20 THEN '13-20'
        ELSE '>20'
    END as prescription_bin,

    -- Combined stratum key (gender|age_bin|condition_bin|prescription_bin)
    COALESCE(pd.Sex, 'U') || '|' ||
    CASE
        WHEN pd.age IS NULL THEN 'unknown'
        WHEN pd.age < 40 THEN '<40'
        WHEN pd.age >= 40 AND pd.age < 60 THEN '40-60'
        WHEN pd.age >= 60 AND pd.age < 75 THEN '60-75'
        ELSE '>75'
    END || '|' ||
    CASE
        WHEN COALESCE(pc.condition_count, 0) <= 10 THEN '0-10'
        WHEN COALESCE(pc.condition_count, 0) <= 25 THEN '11-25'
        WHEN COALESCE(pc.condition_count, 0) <= 50 THEN '26-50'
        ELSE '>50'
    END || '|' ||
    CASE
        WHEN COALESCE(pp.prescription_count, 0) <= 5 THEN '0-5'
        WHEN COALESCE(pp.prescription_count, 0) <= 12 THEN '6-12'
        WHEN COALESCE(pp.prescription_count, 0) <= 20 THEN '13-20'
        ELSE '>20'
    END as stratum_key

FROM patient_demographics pd
LEFT JOIN patient_conditions pc ON pd.FK_Patient_Link_ID = pc.FK_Patient_Link_ID
LEFT JOIN patient_prescriptions pp ON pd.FK_Patient_Link_ID = pp.FK_Patient_Link_ID
