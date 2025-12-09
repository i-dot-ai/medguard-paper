-- Load SMR outcome codes from external CSV file
-- This defines the "SMR outcome" based on the provided input file
CREATE OR REPLACE VIEW {smr_outcomes_view} AS
SELECT
    CAST(CAST(SuppliedCode AS BIGINT) AS VARCHAR) as code
FROM '{smr_outcomes_input_file}'
WHERE 
    category IN ('medication_stopped')
    AND predictable = True