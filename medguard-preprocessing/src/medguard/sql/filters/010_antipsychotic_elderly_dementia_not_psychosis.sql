-- Filter 010: Antipsychotics prescribed for >6 weeks in the over 65s with dementia but not psychosis
--
-- This filter identifies patients who:
-- 1. Are aged >65 years at time of prescription
-- 2. Have a recorded diagnosis of dementia (any type)
-- 3. Have been prescribed an antipsychotic for >6 weeks (>42 days)
-- 4. Do NOT have a diagnosis of psychosis (exclusion criterion)
-- 5. Prescription must occur AFTER dementia diagnosis
--
-- Design decisions:
-- - Uses patient Dob to calculate age at time of prescription
-- - Uses GP Events for dementia and psychosis diagnoses
-- - Uses GP Prescriptions table for medication prescriptions (consolidated prescription islands)
-- - Duration >6 weeks (>42 days) calculated from medication_start_date to medication_end_date
-- - "Not psychosis" = LEFT JOIN with IS NULL pattern to exclude patients with any psychosis diagnosis
-- - Prescription must occur AFTER dementia diagnosis
-- - Antipsychotics: risperidone, olanzapine, quetiapine, haloperidol, aripiprazole, amisulpride, chlorpromazine
-- - Clinical rationale: Antipsychotics increase stroke risk, mortality, cognitive decline in dementia
-- - Only indicated for severe distress/risk of harm from psychosis symptoms
-- - NICE guidance: avoid in dementia unless treating psychosis/severe agitation
-- - Risk level: 3 (significant risk - stroke, mortality, falls, cognitive decline)

WITH dementia_codes AS (
    -- SNOMED codes for dementia and all descendants
    -- Based on concept_id 52448006 (Dementia disorder)
    SELECT code FROM (VALUES
        ('52448006'),   -- Dementia (disorder) [PARENT]
        ('230282000'),  -- Post-traumatic dementia
        ('278857002'),  -- Dementia of frontal lobe type
        ('51928006'),   -- General paresis - neurosyphilis
        ('9345005'),    -- Dialysis dementia
        ('191519005'),  -- Dementia associated with another disease
        ('230289009'),  -- Patchy dementia
        ('26929004'),   -- Alzheimer's disease
        ('22381000119105'), -- Primary degenerative dementia
        ('1591000119103'),  -- Dementia with behavioral disturbance
        ('698949001'),  -- Dementia in remission
        ('713844000'),  -- Dementia co-occurrent with HIV infection
        ('715737004'),  -- Parkinsonism with dementia of Guadeloupe
        ('268612007'),  -- Senile and presenile organic psychotic conditions
        ('12348006'),   -- Presenile dementia
        ('15662003'),   -- Senile dementia
        ('722978000'),  -- Toxic dementia
        ('723390000'),  -- Rapidly progressive dementia
        ('725898002'),  -- Delirium co-occurrent with dementia
        ('762707000'),  -- Subcortical dementia
        ('774069007'),  -- Protein kinase cAMP-dependent type I regulatory subunit beta-related neurodegenerative dementia
        ('788898005'),  -- Dementia caused by volatile inhalant
        ('838276009'),  -- Amyotrophic lateral sclerosis, parkinsonism, dementia complex
        ('58756001'),   -- Huntington's chorea
        ('1186724002'), -- HTRA1-related autosomal dominant cerebral small vessel disease
        ('1186887004'), -- Dementia caused by manganese
        ('1187126002'), -- ITM2B-related amyloidosis
        ('1259584009'), -- Post-dialysis dementia
        ('230270009'),  -- Frontotemporal dementia
        ('1339031006'), -- Dementia caused by ionising radiation
        ('1363185006'), -- Dementia due to Lewy body disease
        ('702429008'),  -- Frontotemporal dementia with parkinsonism-17
        ('1089521000000106'), -- Predominantly cortical dementia
        ('698687007'),  -- Post-traumatic dementia with behavioral change
        ('1187004001'), -- Chronic traumatic encephalopathy
        ('82959004'),   -- Dementia paralytica juvenilis
        ('281004'),     -- Dementia associated with alcoholism
        ('425390006'),  -- Dementia associated with Parkinson's Disease
        ('698624003'),  -- Dementia associated with cerebral lipidosis
        ('698625002'),  -- Dementia associated with normal pressure hydrocephalus
        ('698626001'),  -- Dementia associated with multiple sclerosis
        ('698725008'),  -- Dementia associated with neurosyphilis
        ('698726009'),  -- Dementia associated with viral encephalitis
        ('698781002'),  -- Dementia associated with cerebral anoxia
        ('429998004'),  -- Vascular dementia
        ('722979008'),  -- Dementia due to metabolic abnormality
        ('722980006'),  -- Dementia due to chromosomal anomaly
        ('724776007'),  -- Dementia due to disorder of central nervous system
        ('724777003'),  -- Dementia due to infectious disease
        ('762351006'),  -- Dementia due to and following injury of head
        ('840464007'),  -- Dementia due to carbon monoxide poisoning
        ('1186883000'), -- Dementia due to nutritional deficiency disorder
        ('1259579003'), -- Dementia due to Behcet syndrome
        ('1259581001'), -- Dementia due to coeliac disease
        ('1259591007'), -- Dementia due to acquired hypothyroidism
        ('1259656006'), -- Dementia due to renal failure
        ('1259663006'), -- Dementia due to polyarteritis nodosa
        ('1259661008'), -- Dementia due to inflammatory disorder of musculoskeletal system
        ('1259517005'), -- Dementia due to systemic lupus erythematosus
        ('1259476008'), -- Dementia due to genetic disease
        ('1259465009'), -- Dementia due to hepatic failure
        ('230269008'),  -- Focal Alzheimer's disease
        ('230280008'),  -- Alzheimer's disease with progressive aphasia
        ('416975007'),  -- Primary degenerative dementia of the Alzheimer type, senile onset
        ('416780008'),  -- Primary degenerative dementia of the Alzheimer type, presenile onset
        ('1581000119101'),  -- Dementia of the Alzheimer type with behavioral disturbance
        ('97751000119108'), -- Alzheimer's disease with altered behaviour
        ('141991000119109'), -- Alzheimer's disease with delusions
        ('142001000119106'), -- Alzheimer's disease with depressed mood
        ('142011000119109'), -- Alzheimer's disease with delirium
        ('722600006'),  -- Non-amnestic Alzheimer disease
        ('79341000119107'), -- Mixed dementia
        ('1259128002'), -- Alzheimer's disease with psychosis
        ('288631000119104'), -- Vascular dementia with behavioral disturbance
        ('82381000119103'), -- Epileptic dementia with behavioural disturbance
        ('135811000119107'), -- Lewy body dementia with behavioral disturbance
        ('698948009'),  -- Vascular dementia in remission
        ('698954005'),  -- Primary degenerative dementia of the Alzheimer type, senile onset in remission
        ('698955006'),  -- Primary degenerative dementia of the Alzheimer type, presenile onset in remission
        ('713488003'),  -- Presenile dementia co-occurrent with HIV infection
        ('421529006'),  -- Dementia with AIDS
        ('191451009'),  -- Uncomplicated presenile dementia
        ('191452002'),  -- Presenile dementia with delirium
        ('191454001'),  -- Presenile dementia with paranoia
        ('191455000'),  -- Presenile dementia with depression
        ('31081000119101'), -- Presenile dementia with delusions
        ('1363184005'), -- Early onset dementia due to Lewy body disease
        ('1089501000000102'), -- Presenile dementia with psychosis
        ('191449005'),  -- Uncomplicated senile dementia
        ('191457008'),  -- Senile dementia with depressive or paranoid features
        ('191461002'),  -- Senile dementia with delirium
        ('312991009'),  -- Late onset dementia due to Lewy body disease
        ('371026009'),  -- Senile dementia with psychosis
        ('2421000119107'),  -- Hallucinations co-occurrent and due to late onset dementia
        ('191493005'),  -- Dementia caused by drug
        ('733184002'),  -- Dementia caused by heavy metal exposure
        ('230286002'),  -- Subcortical vascular dementia
        ('230299004'),  -- Juvenile onset Huntington's disease
        ('230300007'),  -- Late onset Huntington's disease
        ('230301006'),  -- Akinetic-rigid form of Huntington's disease
        ('783161005'),  -- ABri amyloidosis
        ('783258000'),  -- Familial dementia Danish type
        ('230274000'),  -- Frontal lobe degeneration with motor neurone disease
        ('702393003'),  -- CHMP2B-related frontotemporal dementia
        ('716667005'),  -- Right temporal lobar atrophy
        ('716994006'),  -- Behavioural variant of frontotemporal dementia
        ('230271008'),  -- Pick's disease with Pick bodies
        ('230272001'),  -- Pick's disease with Pick cells and no Pick bodies
        ('230288001'),  -- Semantic dementia
        ('21921000119103'), -- Dementia co-occurrent and due to Pick's disease
        ('1259124000'), -- Amyotrophic lateral sclerosis with frontotemporal dementia
        ('1259673008'), -- Dementia due to neurofilament inclusion body disease
        ('1260352009'), -- Frontotemporal dementia due to TARDBP mutation
        ('1260353004'), -- Frontotemporal dementia due to VCP mutation
        ('1260354005'), -- Frontotemporal dementia due to C9orf72 mutation
        ('1260355006'), -- Frontotemporal dementia due to FUS mutation
        ('702426001'),  -- GRN-related frontotemporal dementia
        ('1260328002'), -- Familial multiple system deposition of tau protein
        ('101421000119107'), -- Dementia due to Parkinson's disease
        ('82371000119101'), -- Dementia due to multiple sclerosis with altered behavior
        ('733192006'),  -- Dementia due to herpes encephalitis
        ('1259519008'), -- Dementia due to subacute sclerosing panencephalitis
        ('56267009'),   -- Multi-infarct dementia
        ('230285003'),  -- Vascular dementia of acute onset
        ('191464005'),  -- Arteriosclerotic dementia with delirium
        ('191463004'),  -- Uncomplicated arteriosclerotic dementia
        ('191466007'),  -- Arteriosclerotic dementia with depression
        ('191465006'),  -- Arteriosclerotic dementia with paranoia
        ('723123001'),  -- Ischaemic vascular dementia
        ('16276361000119109'), -- Vascular dementia without behavioural disturbance
        ('833326008'),  -- Cortical vascular dementia
        ('1259488005'), -- Dementia due to cerebral amyloid angiopathy
        ('1259485008'), -- Dementia due to cerebral vasculitis
        ('1259499007'), -- Dementia due to hemorrhagic cerebral infarction due to hypertension
        ('1089531000000108'), -- Predominantly cortical vascular dementia
        ('1259531005'), -- Dementia due to hypertensive encephalopathy
        ('1259511006'), -- Dementia due to Wilson disease
        ('1259467001'), -- Dementia due to hypercalcemia
        ('733194007'),  -- Dementia co-occurrent and due to Down syndrome
        ('1259473000'), -- Dementia due to fragile X syndrome
        ('442344002'),  -- Dementia due to Huntington chorea
        ('722977005'),  -- Dementia co-occurrent and due to neurocysticercosis
        ('724992007'),  -- Epilepsy co-occurrent and due to dementia
        ('733190003'),  -- Dementia due to primary malignant neoplasm of brain
        ('733191004'),  -- Dementia due to chronic intracranial subdural hematoma
        ('733193001'),  -- Dementia with progressive multifocal leucoencephalopathy
        ('762350007'),  -- Dementia due to prion disease
        ('789170003'),  -- Disinhibited behavior due to dementia
        ('293671000119109'), -- Behavioral disturbance due to multi-infarct dementia
        ('1259586006'), -- Dementia due to autoimmune encephalitis
        ('1259675001'), -- Dementia due to obstructive hydrocephalus
        ('1259677009'), -- Dementia due to multiple system atrophy
        ('1259679007'), -- Dementia due to atypical pantothenate kinase associated neurodegeneration
        ('1259990004'), -- Dementia due to classical pantothenate kinase associated neurodegeneration
        ('1259667007'), -- Dementia due to paraneoplastic encephalitis
        ('1259492003'), -- Dementia due to metastatic malignant neoplasm to brain
        ('1259494002'), -- Dementia due to leucodystrophy
        ('1259524006'), -- Dementia due to trypanosomiasis
        ('1259513009'), -- Dementia due to Whipple disease
        ('1259496000'), -- Dementia due to Lyme disease
        ('1186879000'), -- Dementia due to thiamine deficiency
        ('1186881003'), -- Dementia due to niacin deficiency
        ('1186880002'), -- Dementia due to cobalamin deficiency
        ('840465008'),  -- Dementia due to iron deficiency
        ('1148924004'), -- Dementia due to deficiency of folic acid
        ('1186877003'), -- Dementia due to vitamin E deficiency
        ('1259480003'), -- Dementia due to fatal familial insomnia
        ('1259478009'), -- Dementia due to familial Creutzfeldt-Jakob disease
        ('1259469003'), -- Dementia due to Gerstmann Straussler Scheinker syndrome
        ('130121000119104') -- Dementia due to Rett syndrome
    ) AS t(code)
),

psychosis_codes AS (
    -- SNOMED codes for psychosis and all descendants
    -- Based on concept_id 69322001 (Psychotic disorder)
    -- Used as EXCLUSION criterion - patients with psychosis are NOT flagged
    SELECT code FROM (VALUES
        ('69322001'),   -- Psychotic disorder [PARENT]
        ('191680007'),  -- Psychogenic paranoid psychosis
        ('18260003'),   -- Postpartum psychosis
        ('58214004'),   -- Schizophrenia
        ('58647003'),   -- Severe mood disorder with psychotic features, mood-congruent
        ('61831009'),   -- Induced psychotic disorder
        ('68890003'),   -- Schizoaffective disorder
        ('191525009'),  -- Non-organic psychosis
        ('231438001'),  -- Presbyophrenic psychosis
        ('129602009'),  -- Symbiotic infantile psychosis
        ('191676002'),  -- Reactive depressive psychosis
        ('408858002'),  -- Infantile psychosis
        ('191447007'),  -- Organic psychotic condition
        ('441704009'),  -- Affective psychosis
        ('231437006'),  -- Reactive psychoses
        ('473452003'),  -- Atypical psychosis
        ('10760421000119102'), -- Psychotic disorder in mother complicating childbirth
        ('10760461000119107'), -- Psychotic disorder in mother complicating pregnancy
        ('719717006'),  -- Psychosis co-occurrent and due to Parkinson's disease
        ('724755002'),  -- Positive symptoms co-occurrent and due to primary psychotic disorder
        ('724756001'),  -- Negative symptoms co-occurrent and due to primary psychotic disorder
        ('724758000'),  -- Manic symptoms co-occurrent and due to primary psychotic disorder
        ('724759008'),  -- Psychomotor symptom co-occurrent and due to psychotic disorder
        ('724760003'),  -- Cognitive impairment co-occurrent and due to primary psychotic disorder
        ('765176007'),  -- Psychosis and severe depression co-occurrent and due to bipolar affective disorder
        ('357705009'),  -- Cotard's syndrome
        ('65971000052100'), -- Acute psychosis
        ('1231503005'), -- Psychotic disorder with insight present
        ('48500005'),   -- Delusional disorder
        ('1087461000000107'), -- Late onset substance-induced psychosis
        ('1089691000000105'), -- Acute predominantly delusional psychotic disorder
        ('237351003'),  -- Mild postnatal psychosis
        ('237352005'),  -- Severe postnatal psychosis
        ('60401000119104'), -- Postpartum psychosis in remission
        ('191527001'),  -- Simple schizophrenia
        ('191542003'),  -- Catatonic schizophrenia
        ('111484002'),  -- Undifferentiated schizophrenia
        ('268617001'),  -- Acute schizophrenic episode
        ('26025008'),   -- Residual schizophrenia
        ('26472000'),   -- Paraphrenia
        ('35252006'),   -- Disorganized schizophrenia
        ('64905009'),   -- Paranoid schizophrenia
        ('83746006'),   -- Chronic schizophrenia
        ('191526005'),  -- Schizophrenic disorders
        ('191577003'),  -- Cenesthopathic schizophrenia
        ('247804008'),  -- Schizophrenic prodrome
        ('416340002'),  -- Late onset schizophrenia
        ('4926007'),    -- Schizophrenia in remission
        ('1204417003'), -- Early onset schizophrenia
        ('1335862003'), -- Childhood-onset schizophrenia
        ('70546001'),   -- Severe bipolar disorder with psychotic features, mood-congruent
        ('63395003'),   -- Folie à trois
        ('270901009'),  -- Schizoaffective disorder, mixed type
        ('271428004'),  -- Schizoaffective disorder, manic type
        ('38368003'),   -- Schizoaffective disorder, bipolar type
        ('84760002'),   -- Schizoaffective disorder, depressive type
        ('191567000'),  -- Schizoaffective schizophrenia
        ('755311000000100'), -- Non-organic psychosis in remission
        ('288751000119101'), -- Reactive depressive psychosis, single episode
        ('1086471000000103'), -- Recurrent reactive depressive episodes, severe, with psychosis
        ('191499009'),  -- Transient organic psychoses
        ('191483003'),  -- Psychotic disorder caused by drug
        ('17262008'),   -- Non-alcoholic Korsakoff's psychosis
        ('231449007'),  -- Epileptic psychosis
        ('371026009'),  -- Senile dementia with psychosis
        ('1259128002'), -- Alzheimer's disease with psychosis
        ('5510009'),    -- Organic delusional disorder
        ('5464005'),    -- Brief reactive psychosis
        ('14291003'),   -- Subchronic disorganized schizophrenia with acute exacerbations
        ('191531007'),  -- Acute exacerbation of chronic schizophrenia
        ('191572009'),  -- Acute exacerbation of chronic schizoaffective schizophrenia
        ('231489001'),  -- Acute transient psychotic disorder
        ('274953007'),  -- Acute polymorphic psychotic disorder
        ('278853003'),  -- Acute schizophrenia-like psychotic disorder
        ('162313000'),  -- Morbid jealousy
        ('231487004'),  -- Persistent delusional disorder
        ('278506006'),  -- Involutional paranoid state
        ('280949006'),  -- Erotomania
        ('14144000'),   -- Erotomanic delusion disorder
        ('47447001'),   -- Grandiose delusion disorder
        ('60123008'),   -- Delusional disorder, mixed type
        ('77475008'),   -- Jealous delusion disorder
        ('89618007'),   -- Persecutory delusion disorder
        ('191667009'),  -- Paranoid disorder
        ('191668004'),  -- Simple paranoid state
        ('191672000'),  -- Paranoia querulans
        ('268622001'),  -- Chronic paranoid psychosis
        ('129604005'),  -- Delusion of heart disease syndrome
        ('698951002'),  -- Delusional disorder in remission
        ('723899008'),  -- Delusional disorder currently symptomatic
        ('65179007'),   -- Koro
        ('755301000000102'), -- Paranoid state in remission
        ('16990005'),   -- Subchronic schizophrenia
        ('111483008'),  -- Catatonic schizophrenia in remission
        ('42868002'),   -- Subchronic catatonic schizophrenia
        ('68995007'),   -- Chronic catatonic schizophrenia
        ('441833000'),  -- Lethal catatonia
        ('1089481000000106'), -- Cataleptic schizophrenia
        ('29599000'),   -- Chronic undifferentiated schizophrenia
        ('39610001'),   -- Undifferentiated schizophrenia in remission
        ('85861002'),   -- Subchronic undifferentiated schizophrenia
        ('51133006'),   -- Residual schizophrenia in remission
        ('71103003'),   -- Chronic residual schizophrenia
        ('76566000'),   -- Subchronic residual schizophrenia
        ('38295006'),   -- Involutional paraphrenia
        ('12939007'),   -- Chronic disorganized schizophrenia
        ('27387000'),   -- Subchronic disorganized schizophrenia
        ('31373002'),   -- Disorganized schizophrenia in remission
        ('31658008'),   -- Chronic paranoid schizophrenia
        ('63181006'),   -- Paranoid schizophrenia in remission
        ('79866005'),   -- Subchronic paranoid schizophrenia
        ('191574005'),  -- Schizoaffective schizophrenia in remission
        ('54761006'),   -- Severe depressed bipolar I disorder with psychotic features, mood-congruent
        ('64731001'),   -- Severe mixed bipolar I disorder with psychotic features, mood-congruent
        ('78640000'),   -- Severe manic bipolar I disorder with psychotic features, mood-congruent
        ('191569002'),  -- Subchronic schizoaffective schizophrenia
        ('191570001'),  -- Chronic schizoaffective schizophrenia
        ('191571002'),  -- Acute exacerbation of subchronic schizoaffective schizophrenia
        ('724655005'),  -- Psychotic disorder caused by opioid
        ('724729003'),  -- Psychotic disorder caused by psychoactive substance
        ('762325009'),  -- Psychotic disorder caused by stimulant
        ('191486006'),  -- Hallucinosis caused by drug
        ('427975003'),  -- Delusional disorder caused by drug
        ('943071000000104'), -- Opioid-induced psychosis
        ('943081000000102'), -- Cannabis-induced psychosis
        ('943091000000100'), -- Sedative-induced psychosis
        ('943101000000108'), -- Cocaine-induced psychosis
        ('943131000000102'), -- Hallucinogen-induced psychosis
        ('278852008'),  -- Paranoid-hallucinatory epileptic psychosis
        ('371024007'),  -- Senile dementia with delusion
        ('54502004'),   -- Primary degenerative dementia of the Alzheimer type, presenile onset, with delusions
        ('55009008'),   -- Primary degenerative dementia of the Alzheimer type, senile onset, with delusions
        ('737225007'),  -- Secondary psychotic syndrome with hallucinations and delusions
        ('31081000119101'), -- Presenile dementia with delusions
        ('191548004'),  -- Acute exacerbation of chronic catatonic schizophrenia
        ('191555002'),  -- Acute exacerbation of chronic paranoid schizophrenia
        ('191678001'),  -- Reactive confusion
        ('268624000'),  -- Acute paranoid reaction
        ('307417003'),  -- Cycloid psychosis
        ('63204009'),   -- Bouffée délirante
        ('712824002'),  -- Acute polymorphic psychotic disorder without symptoms of schizophrenia
        ('712850003'),  -- Acute polymorphic psychotic disorder co-occurrent with symptoms of schizophrenia
        ('88975006'),   -- Schizophreniform disorder
        ('762510005'),  -- Psychotic disorder with schizophreniform symptoms caused by synthetic cathinone
        ('278508007'),  -- Delusional dysmorphophobia
        ('33323008'),   -- Somatic delusion disorder
        ('18573003'),   -- Obsessional erotomania
        ('191485005'),  -- Paranoid state caused by drug
        ('723900003'),  -- Delusional disorder currently in partial remission
        ('723901004'),  -- Delusional disorder currently in full remission
        ('111482003'),  -- Subchronic schizophrenia with acute exacerbations
        ('191547009'),  -- Acute exacerbation of subchronic catatonic schizophrenia
        ('79204003'),   -- Chronic undifferentiated schizophrenia with acute exacerbations
        ('7025000'),    -- Subchronic undifferentiated schizophrenia with acute exacerbations
        ('30336007'),   -- Chronic residual schizophrenia with acute exacerbations
        ('70814008'),   -- Subchronic residual schizophrenia with acute exacerbations
        ('35218008'),   -- Chronic disorganised schizophrenia with acute exacerbation
        ('191554003'),  -- Acute exacerbation of subchronic paranoid schizophrenia
        ('20385005'),   -- Psychotic disorder with delusions caused by opioid
        ('19445006'),   -- Opioid-induced psychotic disorder with hallucinations
        ('737340007'),  -- Psychotic disorder caused by synthetic cannabinoid
        ('75122001'),   -- Inhalant-induced psychotic disorder with delusions
        ('724689006'),  -- Psychotic disorder caused by cocaine
        ('724696008'),  -- Psychotic disorder caused by hallucinogen
        ('724702008'),  -- Psychotic disorder caused by volatile inhalant
        ('762507003'),  -- Psychotic disorder caused by synthetic cathinone
        ('47664006'),   -- Sedative, hypnotic AND/OR anxiolytic-induced psychotic disorder with hallucinations
        ('724673008'),  -- Psychotic disorder caused by sedative
        ('724674002'),  -- Psychotic disorder caused by hypnotic
        ('724675001'),  -- Psychotic disorder caused by anxiolytic
        ('1231846001'), -- Psychosis caused by ethanol
        ('63983005'),   -- Inhalant-induced psychotic disorder with hallucinations
        ('1304290003'), -- Psychotic disorder caused by amphetamine and/or amphetamine derivative
        ('724718002'),  -- Psychotic disorder caused by dissociative drug
        ('32552001')    -- Organic delusional disorder caused by psychoactive substance
    ) AS t(code)
),

antipsychotic_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- These codes match actual UK prescription data
    -- Includes first and second generation antipsychotics commonly used in UK primary care
    SELECT code FROM (VALUES
        -- Parent/international codes (substance level - for reference)
        ('386840002'),  -- Risperidone [PARENT]
        ('386849001'),  -- Olanzapine [PARENT]
        ('386850001'),  -- Quetiapine [PARENT]
        ('386837002'),  -- Haloperidol [PARENT]
        ('386840002'),  -- Aripiprazole [PARENT]
        ('432121000'),  -- Amisulpride [PARENT]
        ('387246007'),  -- Chlorpromazine [PARENT]

        -- UK dm+d codes: Risperidone products (atypical antipsychotic)
        ('38696711000001103'),  -- Risperidone 250microgram tablets
        ('42278711000001101'),  -- Risperidone 1mg tablets
        ('42279211000001103'),  -- Risperidone 500microgram tablets
        ('42278911000001104'),  -- Risperidone 2mg tablets
        ('42279011000001108'),  -- Risperidone 3mg tablets
        ('42279111000001109'),  -- Risperidone 4mg tablets
        ('42279311000001106'),  -- Risperidone 6mg tablets
        ('9045911000001108'),   -- Risperidone 500microgram orodispersible tablets
        ('4054011000001109'),   -- Risperidone 1mg orodispersible tablets
        ('4054111000001105'),   -- Risperidone 2mg orodispersible tablets
        ('11140911000001100'),  -- Risperidone 4mg orodispersible tablets
        ('11140811000001105'),  -- Risperidone 3mg orodispersible tablets

        -- UK dm+d codes: Olanzapine products (atypical antipsychotic)
        ('42276111000001101'),  -- Olanzapine 5mg tablets
        ('42275511000001103'),  -- Olanzapine 10mg tablets
        ('42275611000001104'),  -- Olanzapine 15mg tablets
        ('42275911000001105'),  -- Olanzapine 20mg tablets
        ('42275711000001108'),  -- Olanzapine 2.5mg tablets
        ('42276211000001107'),  -- Olanzapine 7.5mg tablets
        ('42276011000001102'),  -- Olanzapine 5mg orodispersible tablets
        ('42275411000001102'),  -- Olanzapine 10mg orodispersible tablets
        ('42275811000001100'),  -- Olanzapine 20mg orodispersible tablets
        ('19609111000001109'),  -- Olanzapine 10mg orodispersible tablets
        ('19609311000001106'),  -- Olanzapine 15mg orodispersible tablets
        ('19609411000001104'),  -- Olanzapine 20mg orodispersible tablets
        ('19609511000001100'),  -- Olanzapine 5mg orodispersible tablets

        -- UK dm+d codes: Quetiapine products (atypical antipsychotic)
        ('42278311000001100'),  -- Quetiapine 25mg tablets
        ('42278011000001103'),  -- Quetiapine 100mg tablets
        ('39703111000001104'),  -- Quetiapine 150mg tablets
        ('42278211000001108'),  -- Quetiapine 200mg tablets
        ('42278511000001106'),  -- Quetiapine 300mg tablets
        ('42684011000001103'),  -- Quetiapine 400mg tablets
        ('42684111000001102'),  -- Quetiapine 50mg tablets
        ('42278611000001105'),  -- Quetiapine 400mg modified-release tablets
        ('17828611000001101'),  -- Quetiapine 150mg modified-release tablets
        ('42278111000001102'),  -- Quetiapine 200mg modified-release tablets
        ('14042811000001105'),  -- Quetiapine 50mg modified-release tablets
        ('42278411000001107'),  -- Quetiapine 300mg modified-release tablets
        ('39027411000001105'),  -- Quetiapine 600mg modified-release tablets

        -- UK dm+d codes: Haloperidol products (typical antipsychotic)
        ('42273211000001100'),  -- Haloperidol 5mg tablets
        ('42272711000001104'),  -- Haloperidol 10mg tablets
        ('42272911000001102'),  -- Haloperidol 20mg tablets
        ('42273111000001106'),  -- Haloperidol 500microgram tablets
        ('42273011000001105'),  -- Haloperidol 500microgram capsules
        ('42272611000001108'),  -- Haloperidol 1.5mg tablets

        -- UK dm+d codes: Aripiprazole products (atypical antipsychotic)
        ('42268511000001100'),  -- Aripiprazole 5mg tablets
        ('42268111000001109'),  -- Aripiprazole 10mg tablets
        ('42268211000001103'),  -- Aripiprazole 15mg tablets
        ('42268411000001104'),  -- Aripiprazole 30mg tablets
        ('44050811000001109'),  -- Aripiprazole 1mg tablets
        ('44050911000001104'),  -- Aripiprazole 2.5mg tablets

        -- UK dm+d codes: Amisulpride products (atypical antipsychotic)
        ('42267911000001106'),  -- Amisulpride 50mg tablets
        ('42267611000001100'),  -- Amisulpride 100mg tablets
        ('42267711000001109'),  -- Amisulpride 200mg tablets
        ('42267811000001101'),  -- Amisulpride 400mg tablets

        -- UK dm+d codes: Chlorpromazine products (typical antipsychotic)
        ('42269111000001102'),  -- Chlorpromazine 25mg tablets
        ('42269211000001108'),  -- Chlorpromazine 50mg tablets
        ('42268811000001102'),  -- Chlorpromazine 100mg tablets
        ('42268911000001107'),  -- Chlorpromazine 10mg tablets
        ('42269011000001103'),  -- Chlorpromazine 25mg suppositories
        ('42268711000001105')   -- Chlorpromazine 100mg suppositories

        -- Note: This list includes most common oral antipsychotic formulations
        -- Depot/long-acting injections not included (typically given in secondary care)
        -- Covers atypical (risperidone, olanzapine, quetiapine, aripiprazole, amisulpride)
        -- and typical (haloperidol, chlorpromazine) antipsychotics
    ) AS t(code)
),

elderly_patients AS (
    -- Find patients aged >65 years
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        p.Dob
    FROM {patient_view} p
    WHERE p.Dob IS NOT NULL
),

patients_with_dementia AS (
    -- Find patients with dementia diagnosis from GP events
    SELECT DISTINCT
        ge.FK_Patient_Link_ID,
        MIN(ge.EventDate) as earliest_dementia_date
    FROM {gp_events_enriched} ge
    WHERE ge.SuppliedCode IN (SELECT code FROM dementia_codes)
    GROUP BY ge.FK_Patient_Link_ID
),

patients_with_psychosis AS (
    -- Find patients with psychosis diagnosis (for EXCLUSION)
    -- Any psychosis diagnosis at any time excludes the patient
    SELECT DISTINCT
        ge.FK_Patient_Link_ID
    FROM {gp_events_enriched} ge
    WHERE ge.SuppliedCode IN (SELECT code FROM psychosis_codes)
),

elderly_dementia_antipsychotic_prescriptions AS (
    -- Find antipsychotic prescriptions in elderly patients with dementia
    -- Prescription must be AFTER dementia diagnosis, duration >42 days, patient >65 years
    SELECT DISTINCT
        ep.FK_Patient_Link_ID,
        ep.Dob,
        pd.earliest_dementia_date,
        p.medication_start_date,
        p.medication_end_date,
        p.medication_code,
        p.medication_name,
        DATE_DIFF('day', p.medication_start_date, p.medication_end_date) as duration_days,
        DATE_DIFF('year', ep.Dob, p.medication_start_date) as age_at_prescription
    FROM elderly_patients ep
    INNER JOIN patients_with_dementia pd
        ON ep.FK_Patient_Link_ID = pd.FK_Patient_Link_ID
    INNER JOIN {gp_prescriptions} p
        ON ep.FK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE p.medication_code IN (SELECT code FROM antipsychotic_codes)
        -- Prescription occurred when patient was >65 years
        AND DATE_DIFF('year', ep.Dob, p.medication_start_date) > 65
        -- Duration >6 weeks (>42 days)
        AND DATE_DIFF('day', p.medication_start_date, p.medication_end_date) > 42
        -- Prescription started AFTER dementia diagnosis
        AND p.medication_start_date >= pd.earliest_dementia_date
),

inappropriate_antipsychotic_prescriptions AS (
    -- Exclude patients with psychosis diagnosis
    -- These are inappropriate prescriptions: elderly + dementia + antipsychotic >6 weeks + NO psychosis
    SELECT
        edap.FK_Patient_Link_ID,
        edap.medication_start_date,
        edap.medication_end_date,
        edap.medication_code,
        edap.medication_name
    FROM elderly_dementia_antipsychotic_prescriptions edap
    LEFT JOIN patients_with_psychosis pp
        ON edap.FK_Patient_Link_ID = pp.FK_Patient_Link_ID
    WHERE pp.FK_Patient_Link_ID IS NULL  -- Exclude patients with psychosis
)

-- Return patient IDs matching this filter with period dates
SELECT DISTINCT
    FK_Patient_Link_ID,
    10 as filter_id,
    medication_start_date as start_date,
    medication_end_date as end_date
FROM inappropriate_antipsychotic_prescriptions;
