-- Create medication "islands" - continuous prescription periods for each medication
CREATE OR REPLACE TABLE {gp_prescriptions} AS
WITH medication_events AS (
    -- Get all medication events with the pre-computed dates
    SELECT 
        FK_Patient_Link_ID,
        FK_Patient_ID,
        SuppliedCode as medication_code,
        description as medication_name,
        Dosage,
        Units,
        Quantity,
        RepeatMedicationFlag,
        CourseLengthPerIssue,
        computed_start_date as start_date,
        computed_end_date as end_date,
        
        -- Look at previous prescription for same patient/medication
        LAG(computed_end_date) OVER (
            PARTITION BY FK_Patient_Link_ID, SuppliedCode
            ORDER BY computed_start_date
        ) as prev_end_date,
        
        -- Look at next prescription for same patient/medication
        LEAD(computed_start_date) OVER (
            PARTITION BY FK_Patient_Link_ID, SuppliedCode
            ORDER BY computed_start_date
        ) as next_start_date
        
    FROM GPMedicationsEnriched
    WHERE (Deleted = 'N' OR Deleted IS NULL)
        AND computed_start_date IS NOT NULL
        AND SuppliedCode IS NOT NULL
),

medication_islands AS (
    -- Identify island boundaries and propagate island start date
    SELECT 
        *,
        -- Is this the start of a new island? (no previous or gap > {duration_days} days)
        CASE 
            WHEN prev_end_date IS NULL THEN TRUE
            WHEN DATE_DIFF('day', prev_end_date, start_date) > {duration_days} THEN TRUE
            ELSE FALSE
        END as is_island_start,
        
        -- Is this the end of an island? (no next or gap > {duration_days} days)
        CASE 
            WHEN next_start_date IS NULL THEN TRUE
            WHEN DATE_DIFF('day', end_date, next_start_date) > {duration_days} THEN TRUE
            ELSE FALSE
        END as is_island_end
        
    FROM medication_events
),

medication_with_island_id AS (
    -- Assign each prescription to its island using the start date of the island
    SELECT 
        *,
        -- Find the most recent island start at or before this row
        MAX(CASE WHEN is_island_start THEN start_date ELSE NULL END) OVER (
            PARTITION BY FK_Patient_Link_ID, medication_code
            ORDER BY start_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) as island_start_date,
        
        -- For each island, find its end date (we'll need to join this back)
        FIRST_VALUE(CASE WHEN is_island_end THEN end_date ELSE NULL END) OVER (
            PARTITION BY FK_Patient_Link_ID, medication_code
            ORDER BY start_date
            ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING
        ) as island_end_date_temp
        
    FROM medication_islands
),

-- Get the correct end date for each island
island_boundaries AS (
    SELECT 
        FK_Patient_Link_ID,
        medication_code,
        island_start_date,
        MAX(CASE WHEN is_island_end AND start_date >= island_start_date THEN end_date ELSE NULL END) as island_end_date,
        
        -- Aggregate island statistics
        COUNT(*) as prescription_count,
        STRING_AGG(medication_name, ' / ' ORDER BY start_date) as medication_names,
        MODE(medication_name) as typical_medication_name,
        MODE(Dosage) as typical_dosage,
        MODE(Units) as typical_units,
        SUM(TRY_CAST(Quantity AS DECIMAL)) as total_quantity,
        MODE(CourseLengthPerIssue) as average_course_length,
        SUM(CASE WHEN RepeatMedicationFlag = 'Y' THEN 1 ELSE 0 END) as repeat_count,
        MIN(FK_Patient_ID) as FK_Patient_ID
        
    FROM medication_with_island_id
    GROUP BY 
        FK_Patient_Link_ID,
        medication_code,
        island_start_date
),

cte AS (
    SELECT DISTINCT
        FK_Patient_Link_ID,
        medication_code,
        typical_medication_name as medication_name,
        typical_dosage as dosage,
        typical_units as units,
        island_start_date as medication_start_date,
        island_end_date as medication_end_date,
        DATE_DIFF('day', island_start_date, island_end_date) as total_duration_days,
        prescription_count,
        total_quantity,
        average_course_length,
        
        -- Calculate average days between prescriptions
        CASE 
            WHEN prescription_count > 1 THEN 
                DATE_DIFF('day', island_start_date, island_end_date) / (prescription_count - 1)
            ELSE NULL
        END as avg_days_between_prescriptions,
        
        -- Flag if this is primarily a repeat medication
        CASE 
            WHEN repeat_count > prescription_count / 2 THEN TRUE
            ELSE FALSE
        END as is_repeat_medication
        
    FROM island_boundaries
    WHERE island_end_date IS NOT NULL  -- Ensure we have complete islands
    ORDER BY FK_Patient_Link_ID, medication_end_date, medication_start_date
)
SELECT * FROM cte