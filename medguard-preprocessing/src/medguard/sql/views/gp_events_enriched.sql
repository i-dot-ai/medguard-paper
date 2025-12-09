-- Enrich GP Events with SNOMED codes, descriptions, and SMR flags
CREATE OR REPLACE TABLE {gp_events_enriched} AS
WITH cte AS (
    SELECT 
        ge.*,
        -- Reference Coding information
        rc.MainCode as reference_main_code,
        rc.CodingType as reference_coding_type,
        rc.FullDescription as reference_full_description,
        
        -- SNOMED via Reference_Coding
        rc.SnomedCT_ConceptID as snomed_concept_via_coding,
        snomed_via_rc.Term as snomed_term_via_coding,
        snomed_via_rc.Active as snomed_active_via_coding,
        
        -- SNOMED lookup directly from SuppliedCode
        snomed_supplied.ConceptID as snomed_concept_from_supplied,
        snomed_supplied.Term as snomed_term_from_supplied,
        snomed_supplied.Active as snomed_active_from_supplied,
        
        -- Create a 'best description' field that prioritizes available descriptions
        COALESCE(
            snomed_supplied.Term,
            snomed_via_rc.Term,
            'No description available'
        ) as description,

        smr_event.was_smr,
        smr_event.flag_smr
        
    FROM {gp_events_view} ge
    LEFT JOIN {reference_coding_view} rc 
        ON ge.FK_Reference_Coding_ID = rc.PK_Reference_Coding_ID
    LEFT JOIN {reference_snomed_view} snomed_via_rc
        ON rc.FK_Reference_SnomedCT_ID = snomed_via_rc.PK_Reference_SnomedCT_ID
    LEFT JOIN {reference_snomed_view} snomed_supplied
        ON ge.SuppliedCode = snomed_supplied.ConceptID

    -- Join with the SMR Events view
    LEFT JOIN {smr_events_view} smr_event
        ON ge.FK_Patient_Link_ID = smr_event.FK_Patient_Link_ID
        AND ge.EventDate = smr_event.EventDate
)
-- Filter out the common, useless descriptions
SELECT cte.*
FROM cte
LEFT JOIN {gp_events_excluded_description_view} ee
    ON ee.description = cte.description
WHERE ee.description IS NULL