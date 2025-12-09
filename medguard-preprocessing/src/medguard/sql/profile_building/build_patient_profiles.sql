-- Final query to assemble patient profiles
WITH {ctes}
SELECT 
    -- Patient Link fields
    pb.PK_Patient_Link_ID,
    pb.Deceased,
    pb.DeathDate,
    pb.Restricted,
    pb.DateOfRegistration,
    -- Patient demographic fields
    pb.PK_Patient_ID,
    pb.CreateDate,
    pb.Dob,
    pb.Sex,
    pb.EthnicOrigin,
    pb.IMD_Score,
    pb.FrailtyScore,
    pb.QOFRegisters,
    pb.FrailtyDeficitList,
    pb.MortalityRiskScore,
    pb.SocialCareFlag{select_fields}
FROM patient_batch pb
{joins}
ORDER BY pb.PK_Patient_Link_ID