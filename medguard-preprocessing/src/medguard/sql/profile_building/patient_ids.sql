-- CTE for patient IDs we're processing
patient_ids AS (
    SELECT value::BIGINT as PK_Patient_Link_ID 
    FROM (VALUES {patient_id_values}) AS t(value)
)