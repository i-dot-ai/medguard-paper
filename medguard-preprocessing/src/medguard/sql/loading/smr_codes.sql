-- Load SMR codes from external CSV file
-- This defines "what counts as an SMR" based on the provided input file
CREATE OR REPLACE VIEW {smr_codes_view} AS
SELECT DISTINCT CAST(CAST(code AS BIGINT) AS VARCHAR) as code
FROM '{smr_codes_input_file}'