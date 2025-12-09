-- Load negative SMR outcome codes from external CSV file
CREATE OR REPLACE VIEW {smr_negative_outcomes_view} AS
SELECT CAST(CAST(SuppliedCode AS BIGINT) AS VARCHAR) as code
FROM '{smr_negative_outcomes_input_file}'