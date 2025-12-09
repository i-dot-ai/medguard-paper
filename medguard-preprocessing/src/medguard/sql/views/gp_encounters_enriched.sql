-- Enrich GP Encounters with SNOMED codes and descriptions
CREATE OR REPLACE VIEW {gp_encounters_enriched} AS
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
    ) as description
    
FROM {gp_encounters_view} ge
LEFT JOIN {reference_coding_view} rc 
    ON ge.FK_Reference_Coding_ID = rc.PK_Reference_Coding_ID
LEFT JOIN {reference_snomed_view} snomed_via_rc
    ON rc.FK_Reference_SnomedCT_ID = snomed_via_rc.PK_Reference_SnomedCT_ID
LEFT JOIN {reference_snomed_view} snomed_supplied
    ON ge.SuppliedCode = snomed_supplied.ConceptID