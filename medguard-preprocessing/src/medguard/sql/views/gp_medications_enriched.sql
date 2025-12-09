-- Enrich GP Medications with SNOMED descriptions and computed dates
CREATE OR REPLACE VIEW {gp_medications_enriched} AS
SELECT 
    gm.*,
    -- Reference Coding information
    rc.MainCode as reference_main_code,
    rc.CodingType as reference_coding_type,
    rc.FullDescription as reference_full_description,
    
    -- SNOMED information
    snomed_via_rc.Term as snomed_term_via_coding,
    snomed_supplied.Term as snomed_term_from_supplied,
    
    -- Best description for medications
    COALESCE(
        snomed_supplied.Term,
        snomed_via_rc.Term,
        'No description available'
    ) as description,
    
    -- Smart date logic
    COALESCE(
        gm.MedicationStartDate,
        gm.MedicationDate
    ) as computed_start_date,
    
    COALESCE(
        gm.MedicationEndDate,
        -- If we have CourseLengthPerIssue, add it to computed start date
        CASE
            WHEN gm.CourseLengthPerIssue IS NOT NULL AND gm.CourseLengthPerIssue != ''
                AND TRY_CAST(gm.CourseLengthPerIssue AS INTEGER) IS NOT NULL
            THEN COALESCE(gm.MedicationStartDate, gm.MedicationDate) + (TRY_CAST(gm.CourseLengthPerIssue AS INTEGER) * INTERVAL '1 day')
            -- Otherwise add 30 days to computed start date
            ELSE COALESCE(gm.MedicationStartDate, gm.MedicationDate) + INTERVAL '30 days'
        END
    ) as computed_end_date,
    
    -- Computed duration in days (cast date difference to integer)
    CASE 
        WHEN gm.MedicationEndDate IS NOT NULL THEN
            CAST((gm.MedicationEndDate - COALESCE(gm.MedicationStartDate, gm.MedicationDate)) AS INTEGER)
        WHEN gm.CourseLengthPerIssue IS NOT NULL AND gm.CourseLengthPerIssue != ''
            AND TRY_CAST(gm.CourseLengthPerIssue AS INTEGER) IS NOT NULL
        THEN TRY_CAST(gm.CourseLengthPerIssue AS INTEGER)
        ELSE 30
    END as computed_duration_days
    
FROM {gp_medications_view} gm
LEFT JOIN {reference_coding_view} rc 
    ON gm.FK_Reference_Coding_ID = rc.PK_Reference_Coding_ID
LEFT JOIN {reference_snomed_view} snomed_via_rc
    ON rc.FK_Reference_SnomedCT_ID = snomed_via_rc.PK_Reference_SnomedCT_ID
LEFT JOIN {reference_snomed_view} snomed_supplied
    ON gm.SuppliedCode = snomed_supplied.ConceptID