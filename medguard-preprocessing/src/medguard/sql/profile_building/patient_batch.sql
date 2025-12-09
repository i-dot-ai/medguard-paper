-- CTE for valid patients with demographics
patient_batch AS (
    WITH first_patient_records AS (
        SELECT 
            p.*,
            ROW_NUMBER() OVER (
                PARTITION BY p.FK_Patient_Link_ID 
                ORDER BY p.PK_Patient_ID
            ) as rn
        FROM {patient_view} p
        WHERE p.FK_Patient_Link_ID IS NOT NULL
            AND p.FK_Reference_Tenancy_ID = 2
    )
    SELECT 
        pl.PK_Patient_Link_ID,
        pl.Deceased,
        pl.DeathDate,
        pl.Restricted,
        pl.DateOfRegistration,
        -- Get demographics from Patient table if available
        p.PK_Patient_ID,
        p.CreateDate,
        p.Dob,
        p.Sex,
        p.EthnicOrigin,
        p.IMD_Score,
        p.FrailtyScore,
        p.QOFRegisters,
        p.FrailtyDeficitList,
        p.MortalityRiskScore,
        p.SocialCareFlag
    FROM {patient_link_view} pl
    INNER JOIN patient_ids pi ON pl.PK_Patient_Link_ID = pi.PK_Patient_Link_ID
    LEFT JOIN first_patient_records p 
        ON pl.PK_Patient_Link_ID = p.FK_Patient_Link_ID 
        AND p.rn = 1
    ORDER BY pl.PK_Patient_Link_ID
)