-- Sample patients with at least one SMR event
SELECT DISTINCT pl.PK_Patient_Link_ID
FROM {patient_link_view} pl
INNER JOIN {smr_patients_view} ps
    ON pl.PK_Patient_Link_ID = ps.FK_Patient_Link_ID
WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
    AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
    {deceased_filter}
    AND ps.has_an_smr = TRUE
ORDER BY pl.PK_Patient_Link_ID
LIMIT {limit}
OFFSET {offset}