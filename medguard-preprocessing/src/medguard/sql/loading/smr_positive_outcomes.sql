-- Load positive SMR outcome codes from external CSV file
CREATE OR REPLACE VIEW {smr_positive_outcomes_view} AS
SELECT CAST(CAST(SuppliedCode AS BIGINT) AS VARCHAR) as code
FROM '{smr_positive_outcomes_input_file}'