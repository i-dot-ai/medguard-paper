-- Sample balanced 50/50 split of SMR patients with/without medication changes
WITH 
-- Patients who have at least one SMR with medication changes
patients_with_any_changes AS (
    SELECT DISTINCT FK_Patient_Link_ID
    FROM {smr_medications_table}
),

-- Patients with SMRs who have medication changes
smr_with_changes AS (
    SELECT DISTINCT pl.PK_Patient_Link_ID
    FROM {patient_link_view} pl
    INNER JOIN patients_with_any_changes pwc
        ON pl.PK_Patient_Link_ID = pwc.FK_Patient_Link_ID
    WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
        AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
        {deceased_filter}
    ORDER BY RANDOM()
    LIMIT {half_limit_with_remainder}
    OFFSET {half_offset}
),

-- Patients with SMRs who NEVER have medication changes
smr_without_any_changes AS (
    SELECT DISTINCT pl.PK_Patient_Link_ID
    FROM {patient_link_view} pl
    INNER JOIN {smr_patients_view} ps
        ON pl.PK_Patient_Link_ID = ps.FK_Patient_Link_ID
    LEFT JOIN patients_with_any_changes pwc
        ON pl.PK_Patient_Link_ID = pwc.FK_Patient_Link_ID
    WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
        AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
        {deceased_filter}
        AND ps.has_an_smr = TRUE
        AND pwc.FK_Patient_Link_ID IS NULL  -- No medication changes ever
    ORDER BY RANDOM()
    LIMIT {half_limit}
    OFFSET {half_offset}
)

SELECT PK_Patient_Link_ID FROM (
    SELECT * FROM smr_with_changes
    UNION ALL
    SELECT * FROM smr_without_any_changes
) combined
ORDER BY PK_Patient_Link_ID