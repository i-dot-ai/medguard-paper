-- Identify SMR events and their outcomes (positive/negative)
CREATE OR REPLACE TABLE {smr_events_view} AS
WITH is_smr_cte AS (
    SELECT DISTINCT
        FK_Patient_Link_ID,
        EventDate,
        TRUE as was_smr
    FROM {gp_events_view} gp
    INNER JOIN SMRCodes c ON c.code = gp.SuppliedCode
),

positive_outcome_cte AS (
    SELECT DISTINCT
        FK_Patient_Link_ID,
        EventDate,
        TRUE as has_positive
    FROM {gp_events_view} gp
    INNER JOIN {smr_positive_outcomes_view} c ON c.code = gp.SuppliedCode
),

negative_outcome_cte AS (
    SELECT DISTINCT
        FK_Patient_Link_ID,
        EventDate,
        TRUE as has_negative
    FROM {gp_events_view} gp
    INNER JOIN {smr_negative_outcomes_view} c ON c.code = gp.SuppliedCode
),

medication_stopped_cte AS (
    SELECT DISTINCT
        FK_Patient_Link_ID,
        smr_date as EventDate,
        TRUE as any_stopped
    FROM {smr_medications_table}
    WHERE change_type = 'stopped'
),

medication_started_cte AS (
    SELECT DISTINCT
        FK_Patient_Link_ID,
        smr_date as EventDate,
        TRUE as any_started
    FROM {smr_medications_table}
    WHERE change_type = 'started'
),

all_events_cte AS (
    SELECT DISTINCT
        FK_Patient_Link_ID,
        EventDate
    FROM {gp_events_view}
),

smr_events AS (
    SELECT
        e.FK_Patient_Link_ID,
        e.EventDate,
        COALESCE(s.was_smr, FALSE) as was_smr,
        CASE
            WHEN s.was_smr IS NULL OR s.was_smr = FALSE THEN NULL
            WHEN p.has_positive = TRUE THEN TRUE
            WHEN n.has_negative = TRUE THEN FALSE
            ELSE NULL -- SMR but no outcome
        END as flag_smr,

        CASE
            WHEN s.was_smr = TRUE THEN COALESCE(ms.any_stopped, FALSE)
            ELSE NULL
        END as any_medication_stopped,

        CASE
            WHEN s.was_smr = TRUE THEN COALESCE(mst.any_started, FALSE)
            ELSE NULL
        END as any_medication_started

    FROM all_events_cte e
    LEFT JOIN is_smr_cte s ON
        s.FK_Patient_Link_ID = e.FK_Patient_Link_ID AND
        s.EventDate = e.EventDate
    LEFT JOIN positive_outcome_cte p ON
        p.FK_Patient_Link_ID = e.FK_Patient_Link_ID AND
        p.EventDate = e.EventDate
    LEFT JOIN negative_outcome_cte n ON
        n.FK_Patient_Link_ID = e.FK_Patient_Link_ID AND
        n.EventDate = e.EventDate
    LEFT JOIN medication_stopped_cte ms ON
        ms.FK_Patient_Link_ID = e.FK_Patient_Link_ID AND
        ms.EventDate = e.EventDate
    LEFT JOIN medication_started_cte mst ON
        mst.FK_Patient_Link_ID = e.FK_Patient_Link_ID AND
        mst.EventDate = e.EventDate
)

SELECT * FROM smr_events