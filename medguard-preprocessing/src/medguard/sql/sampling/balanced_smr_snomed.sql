-- Sample balanced 50/50 split of SMR patients with positive vs negative SNOMED outcomes
WITH 
with_outcome AS (
    SELECT pl.PK_Patient_Link_ID
    FROM {patient_link_view} pl
    INNER JOIN {smr_patients_view} ps
        ON pl.PK_Patient_Link_ID = ps.FK_Patient_Link_ID
    WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
        AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
        {deceased_filter}
        AND ps.has_an_smr = TRUE
        AND ps.has_positive_outcome = TRUE
    ORDER BY RANDOM()
    LIMIT {half_limit_with_remainder}
    OFFSET {half_offset}
),
without_outcome AS (
    SELECT pl.PK_Patient_Link_ID
    FROM {patient_link_view} pl
    INNER JOIN {smr_patients_view} ps
        ON pl.PK_Patient_Link_ID = ps.FK_Patient_Link_ID
    WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
        AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
        {deceased_filter}
        AND ps.has_an_smr = TRUE
        AND ps.has_negative_outcome = TRUE
    ORDER BY RANDOM()
    LIMIT {half_limit}
    OFFSET {half_offset}
)
SELECT PK_Patient_Link_ID FROM (
    SELECT * FROM with_outcome
    UNION ALL
    SELECT * FROM without_outcome
) combined
ORDER BY PK_Patient_Link_ID