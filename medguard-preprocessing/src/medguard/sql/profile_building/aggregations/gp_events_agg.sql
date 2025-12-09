-- GP Events aggregation CTE with grouping by date
{agg_name}_agg AS (
    SELECT 
        {patient_link_col} as PK_Patient_Link_ID,
        JSON_GROUP_ARRAY(
            JSON_OBJECT(
                'Date', EventDate,
                'was_smr', was_smr,
                'flag_smr', flag_smr,
                'observations', events_array
            )
        ) as {agg_name}
    FROM (
        SELECT 
            {patient_link_col},
            EventDate,
            -- Use COALESCE to convert NULL to FALSE
            COALESCE(CAST(MAX(CAST(was_smr AS INTEGER)) as BOOLEAN), FALSE) as was_smr,
            COALESCE(CAST(MAX(CAST(flag_smr AS INTEGER)) as BOOLEAN), FALSE) as flag_smr,
            JSON_GROUP_ARRAY(
                JSON_OBJECT(
                    'description', description,
                    'Units', Units,
                    'Value', Value,
                    'Episodicity', Episodicity
                )
            ) as events_array
        FROM {view_name}
        WHERE {patient_link_col} IN (SELECT PK_Patient_Link_ID FROM patient_batch)
            {filter_clause}
        GROUP BY {patient_link_col}, EventDate
    ) grouped_events
    GROUP BY {patient_link_col}
)