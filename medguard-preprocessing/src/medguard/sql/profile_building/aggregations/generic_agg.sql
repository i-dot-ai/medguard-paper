-- Generic aggregation CTE template
{agg_name}_agg AS (
    SELECT 
        {patient_link_col} as PK_Patient_Link_ID,
        JSON_GROUP_ARRAY({json_object}) as {agg_name}
    FROM {view_name}
    WHERE {patient_link_col} IN (SELECT PK_Patient_Link_ID FROM patient_batch)
        {filter_clause}
    GROUP BY {patient_link_col}
)