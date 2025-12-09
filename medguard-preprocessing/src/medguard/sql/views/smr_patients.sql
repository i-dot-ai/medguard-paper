-- Aggregate SMR information at the patient level
CREATE OR REPLACE TABLE {smr_patients_view} AS 
WITH patient_smr_stats AS (
    SELECT 
        FK_Patient_Link_ID,
        MAX(CAST(was_smr AS INTEGER)) as has_an_smr,
        MAX(CASE WHEN flag_smr = TRUE THEN 1 ELSE 0 END) as has_positive_outcome,
        MAX(CASE WHEN flag_smr = FALSE THEN 1 ELSE 0 END) as has_negative_outcome
    FROM {smr_events_view}
    GROUP BY FK_Patient_Link_ID
)

SELECT
    FK_Patient_Link_ID,
    CAST(has_an_smr AS BOOLEAN) as has_an_smr,
    CAST(has_positive_outcome AS BOOLEAN) as has_positive_outcome,
    CAST(has_negative_outcome AS BOOLEAN) as has_negative_outcome
FROM patient_smr_stats