-- Load descriptions to exclude from GP events analysis
CREATE OR REPLACE VIEW {gp_events_excluded_description_view} AS 
SELECT DISTINCT description
FROM '{gp_events_excluded_description_input_file}'