-- Sample all valid patients
SELECT PK_Patient_Link_ID
FROM {patient_link_view}
WHERE (Merged != 'Y' OR Merged IS NULL)
    AND (Deleted != 'Y' OR Deleted IS NULL)
    {deceased_filter}
ORDER BY PK_Patient_Link_ID
LIMIT {limit}
OFFSET {offset}