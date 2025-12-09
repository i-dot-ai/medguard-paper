-- Sample patients who DO NOT match any of the PINCER filters
-- Excludes patients found in the excluded_patient_ids set
SELECT pl.PK_Patient_Link_ID
FROM {patient_link_view} pl
WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
    AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
    {deceased_filter}
    AND pl.PK_Patient_Link_ID NOT IN ({excluded_patient_ids})
ORDER BY RANDOM()
LIMIT {limit}
OFFSET {offset}
