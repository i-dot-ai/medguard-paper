# PINCER Medication Safety Filter Guidelines

This document provides guidance for creating medication safety filters for the MedGuard system. These filters implement the PINCER methodology to identify potentially hazardous prescribing patterns in UK general practice data.

## Core Principles

### 1. Precision Over Recall

**Prioritize precision (true positives) over recall (finding all cases).**

- Only flag patients when you have high confidence the filter criteria are met
- False positives create unnecessary clinical workload and reduce trust in the system
- It's acceptable to miss edge cases if it means avoiding false alarms
- Use strict matching criteria and overlapping date logic
- When in doubt, err on the side of NOT flagging a patient

**Example:** For co-prescription checks, require PPI to overlap the NSAID prescription period, not just be prescribed "around the same time."

### 2. UK SNOMED CT Extension (dm+d) Codes

**CRITICAL: UK prescription data uses UK-specific medication product codes, NOT international SNOMED codes.**

#### The Problem
- **International SNOMED CT codes** are 6-9 digit codes representing substances (e.g., `387207008` = "Ibuprofen substance")
- **UK SNOMED CT Extension codes** are 13-15 digit codes containing `1000001` representing specific medication products (e.g., `42104811000001109` = "Ibuprofen 200mg tablet")
- UK prescription data (`GPPrescriptions` table) uses **UK dm+d codes only**
- Filters using international codes will return ZERO results or miss most patients

#### The Solution
1. **Always include UK dm+d codes** for any medication in your filter
2. Use the SNOMED MCP tool with **UK Monolith Edition** to search for medications
3. Extract ALL UK dm+d codes (13-15 digits containing '1000001') from search results
4. Include parent/international codes for reference, but they won't match prescriptions
5. Include codes for ALL common formulations (tablets, capsules, suspensions, gels, etc.)
6. Include codes for ALL common strengths (e.g., 10mg, 20mg, 40mg)

#### How to Collect UK dm+d Codes

```python
# Use SNOMED MCP tool with uk_extension_only parameter:
mcp__snomed-code__search_api_search_get(
    q="ibuprofen",
    uk_extension_only=True,  # ← Returns ONLY UK dm+d codes!
    limit=100
)

# Results will contain ONLY UK medication product codes:
# - 42104811000001109 - Ibuprofen 200mg tablet
# - 42104911000001104 - Ibuprofen 400mg tablet
# - 42105311000001101 - Ibuprofen 600mg tablet
# - 41740811000001103 - Ibuprofen 5% gel
# etc.

# No manual filtering required - all codes contain '1000001'
```

#### Example Code Structure

```sql
medication_codes AS (
    SELECT code FROM (VALUES
        -- Parent/international codes (for reference - won't match prescriptions)
        ('387207008'),  -- Ibuprofen (substance)

        -- UK dm+d codes (THESE MATCH PRESCRIPTIONS)
        ('42104911000001104'),  -- Ibuprofen 400mg tablet
        ('42104811000001109'),  -- Ibuprofen 200mg tablet
        ('42104711000001101'),  -- Ibuprofen 200mg capsule
        ('42105311000001101'),  -- Ibuprofen 600mg tablet
        ('41740811000001103'),  -- Ibuprofen 5% gel
        -- ... continue for all formulations
    ) AS t(code)
)
```

### 3. Temporal Logic and Date Handling

**All filters must track temporal periods when filter criteria are met.**

#### Required Output Format
```sql
SELECT DISTINCT
    FK_Patient_Link_ID,
    '001' as filter_id,  -- Three-digit filter identifier
    start_date,          -- When the hazardous situation started
    end_date             -- When the hazardous situation ended (or present)
FROM final_filter_matches;
```

#### Temporal Matching Rules
- **After diagnosis:** Use `>=` for events that must occur after a diagnosis date
- **Overlapping prescriptions:** Check both start and end dates overlap
  ```sql
  -- PPI overlaps with NSAID if:
  ppi.start_date <= nsaid.end_date
  AND ppi.end_date >= nsaid.start_date
  ```
- **Co-prescription windows:** Define appropriate grace periods (e.g., 28 days for medication reviews)

#### DuckDB Date/Time Syntax Requirements

**IMPORTANT: Use DuckDB's DATE_DIFF function for all date calculations**

```sql
-- ✅ CORRECT: Calculate age from date of birth
DATE_DIFF('year', patient.Dob, CURRENT_DATE)

-- ❌ WRONG: Don't use CAST on INTERVAL
CAST((CURRENT_DATE - patient.Dob) / 365.25 AS INTEGER)

-- ✅ CORRECT: Calculate prescription duration in days
DATE_DIFF('day', medication_start_date, medication_end_date)

-- ❌ WRONG: Don't use CAST on date subtraction
CAST((medication_end_date - medication_start_date) AS INTEGER)

-- ✅ CORRECT: Date arithmetic for lookback periods
medication_start_date - INTERVAL '450 days'

-- Available DATE_DIFF units: 'year', 'month', 'day', 'hour', 'minute', 'second'
```

### 4. Data Source Selection

#### Use GPPrescriptions Table for Medications
- **DO use:** `GPPrescriptions` table (consolidated prescription "islands")
- **DON'T use:** Raw `SharedCare_GP_Medications` events
- **Why:** GPPrescriptions consolidates overlapping prescriptions into continuous periods with `medication_start_date` and `medication_end_date`
- **Columns:** `FK_Patient_Link_ID`, `medication_code`, `medication_name`, `medication_start_date`, `medication_end_date`

#### Use GP Events for Clinical Diagnoses
- **Use:** `{gp_events_enriched}` for diagnoses, observations, clinical events
- **Columns:** `FK_Patient_Link_ID`, `SuppliedCode`, `EventDate`
- **Why:** GP Events contain SNOMED-coded clinical observations

#### Patient Demographics Schema

**SharedCare_Patient Table - Key Columns:**
```sql
-- ✅ CORRECT column names to use:
p.FK_Patient_Link_ID   -- Patient identifier
p.Dob                  -- Date of birth (TIMESTAMP)
p.Sex                  -- Patient sex
p.NhsNo               -- NHS number

-- ❌ WRONG: These columns DO NOT exist:
p.YearOfBirth         -- Does not exist - use Dob instead
p.DateOfBirth         -- Does not exist - use Dob instead
```

**Example: Calculate patient age**
```sql
elderly_patients AS (
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        p.Dob,
        DATE_DIFF('year', p.Dob, CURRENT_DATE) as age
    FROM {patient_view} p
    WHERE p.Dob IS NOT NULL
        AND DATE_DIFF('year', p.Dob, CURRENT_DATE) >= 75
)
```

### 5. Filter Structure Template

Every filter should follow this structure:

```sql
-- Filter XXX: [Brief description of what this filter identifies]
--
-- This filter identifies patients who:
-- 1. [First criterion]
-- 2. [Second criterion]
-- 3. [Third criterion]
--
-- Design decisions:
-- - [Key decision 1]
-- - [Key decision 2]
-- - [Precision vs recall tradeoffs]

WITH condition_codes AS (
    -- IMPORTANT: This list includes UK SNOMED CT Extension codes (dm+d codes)
    -- UK dm+d codes are 13-15 digit codes containing '1000001'
    -- These codes match actual UK prescription data
    SELECT code FROM (VALUES
        -- Parent/international codes (for reference)
        ('123456789'),  -- Condition name [PARENT]

        -- UK dm+d codes (THESE MATCH PRESCRIPTIONS!)
        ('42123456789001100')  -- Specific product
    ) AS t(code)
),

patients_with_condition AS (
    -- Identify patients meeting first criterion
    SELECT DISTINCT
        FK_Patient_Link_ID,
        MIN(EventDate) as condition_date
    FROM {gp_events_enriched}
    WHERE SuppliedCode IN (SELECT code FROM condition_codes)
    GROUP BY FK_Patient_Link_ID
),

medication_codes AS (
    -- IMPORTANT: Include UK dm+d codes
    SELECT code FROM (VALUES
        ('372733002'),  -- Medication [PARENT]
        ('42381311000001109')  -- Specific medication product
    ) AS t(code)
),

patients_with_medication AS (
    -- Identify medication prescriptions
    SELECT DISTINCT
        p.FK_Patient_Link_ID,
        p.medication_start_date,
        p.medication_end_date,
        p.medication_name,
        DATE_DIFF('day', p.medication_start_date, p.medication_end_date) as duration_days
    FROM {gp_prescriptions} p
    WHERE p.medication_code IN (SELECT code FROM medication_codes)
),

final_matches AS (
    -- Apply temporal logic and exclusions
    SELECT DISTINCT
        c.FK_Patient_Link_ID,
        m.medication_start_date as start_date,
        m.medication_end_date as end_date
    FROM patients_with_condition c
    INNER JOIN patients_with_medication m
        ON c.FK_Patient_Link_ID = m.FK_Patient_Link_ID
    WHERE m.medication_start_date >= c.condition_date
        -- Use DATE_DIFF for date calculations
        AND DATE_DIFF('day', c.condition_date, m.medication_start_date) <= 365
)

-- Return results
SELECT DISTINCT
    FK_Patient_Link_ID,
    'XXX' as filter_id,
    start_date,
    end_date
FROM final_matches;
```

### 6. Systematic Code Collection Process

For each medication in your filter:

1. **Search SNOMED MCP tool** (UK Monolith Edition)
   - Search by generic name (e.g., "omeprazole")
   - **Use `uk_extension_only=True` parameter** to get only UK dm+d codes
   - Set limit to 100+ to get all variants
   ```python
   mcp__snomed-code__search_api_search_get(
       q="omeprazole",
       uk_extension_only=True,  # Filters to only UK codes
       limit=100
   )
   ```

2. **Review UK dm+d codes**
   - All results will automatically contain `1000001` (UK namespace)
   - Extract `concept_id` and `preferred_term` from results
   - No manual filtering needed!

3. **Group by medication class**
   - Organize codes by drug (ibuprofen, naproxen, etc.)
   - Include all formulations (tablets, capsules, suppositories, gels, creams, suspensions)
   - Include all strengths (10mg, 20mg, 40mg, etc.)

4. **Document in SQL**
   - Add clear comments for each medication group
   - Include strength and formulation in comments
   - Keep parent codes for reference at the top

### 7. Common Medication Classes

When building filters involving these medication classes, ensure comprehensive UK dm+d coverage:

#### NSAIDs (Non-selective)
- Ibuprofen, naproxen, diclofenac, aspirin (>75mg)
- Indometacin, piroxicam, mefenamic acid, ketoprofen
- Flurbiprofen, aceclofenac, sulindac
- **Exclude:** COX-2 selective inhibitors (celecoxib, etoricoxib, etc.)

#### Proton Pump Inhibitors (PPIs)
- Omeprazole, lansoprazole, pantoprazole
- Esomeprazole, rabeprazole
- Include: magnesium/sodium salt variants

#### Beta Blockers
- Non-selective: propranolol, carvedilol, labetalol, sotalol
- Cardio-selective: metoprolol, bisoprolol, atenolol, nebivolol
- **Note:** Specify if filter requires non-selective only

#### ACE Inhibitors
- Ramipril, lisinopril, perindopril, enalapril
- Include: all salt forms

#### Loop Diuretics
- Furosemide, bumetanide, torasemide

### 8. Testing and Validation

Before finalizing a filter:

1. **Test on subset of data**
   - Check that filter returns reasonable number of patients
   - Literature suggests typical prevalence for PINCER filters: 0.1% - 2% of population

2. **Verify UK dm+d codes match**
   ```sql
   -- Test query to check code matches
   SELECT SuppliedCode, COUNT(*) as prescription_count
   FROM SharedCare_GP_Events
   WHERE SuppliedCode IN (SELECT code FROM medication_codes)
   GROUP BY SuppliedCode
   ORDER BY prescription_count DESC;
   ```

3. **Check temporal logic**
   - Manually review 5-10 flagged patients
   - Verify start_date and end_date make clinical sense
   - Ensure overlapping prescription logic works correctly

4. **Document expected prevalence**
   - Add comment with expected % of population
   - Note if filter returns zero or unexpected results

### 9. Placeholder Variables

Filters use Python string formatting placeholders:

```sql
-- ✅ CORRECT placeholders:
FROM {patient_view}           -- SharedCare_Patient (SINGULAR!)
FROM {gp_prescriptions}       -- GPPrescriptions (medication islands)
FROM {gp_events_enriched}     -- GPEventsEnriched (SNOMED-coded events)
FROM {gp_medications}         -- SharedCare_GP_Medications (raw prescriptions)

-- ❌ WRONG placeholders:
FROM {patients_view}          -- Does not exist - use {patient_view}
FROM {patient}                -- Does not exist - use {patient_view}
```

**Important:**
- Use singular `{patient_view}` NOT `{patients_view}`
- Use lowercase with underscores
- Check `data_processor.py` for available placeholders

### 10. Filter Numbering and Metadata

```python
# In models.py FilterType enum:
FILTER_001 = "001"  # Peptic ulcer + NSAID without PPI
FILTER_002 = "002"  # Asthma + beta blocker
FILTER_003 = "003"  # Elderly ACE/loop without renal check

# In models.py filter_descriptions:
filter_descriptions = {
    FilterType.FILTER_001: "Peptic ulcer + NSAID without PPI co-prescription",
    # ...
}
```

## Common Pitfalls to Avoid

### ❌ Using International SNOMED Codes Only
```sql
-- WRONG - Will match zero prescriptions in UK data
('387207008'),  -- Ibuprofen
```

### ✅ Including UK dm+d Codes
```sql
-- CORRECT - Matches actual UK prescriptions
('387207008'),  -- Ibuprofen (parent - for reference)
('42104811000001109'),  -- Ibuprofen 200mg tablet (matches prescriptions!)
('42104911000001104'),  -- Ibuprofen 400mg tablet (matches prescriptions!)
```

### ❌ Wrong Column Names
```sql
-- WRONG - These columns don't exist
SELECT p.YearOfBirth, p.DateOfBirth
FROM {patient_view} p
```

### ✅ Correct Column Names
```sql
-- CORRECT - Use actual schema columns
SELECT p.Dob, DATE_DIFF('year', p.Dob, CURRENT_DATE) as age
FROM {patient_view} p
```

### ❌ Wrong Date Calculation Syntax
```sql
-- WRONG - Can't cast INTERVAL to INTEGER in DuckDB
CAST((CURRENT_DATE - p.Dob) / 365.25 AS INTEGER)
CAST((end_date - start_date) AS INTEGER)
```

### ✅ Correct DuckDB Date Syntax
```sql
-- CORRECT - Use DATE_DIFF function
DATE_DIFF('year', p.Dob, CURRENT_DATE)
DATE_DIFF('day', start_date, end_date)
```

### ❌ Vague Temporal Logic
```sql
-- WRONG - Too permissive
WHERE medication_date IS NOT NULL
```

### ✅ Precise Temporal Logic
```sql
-- CORRECT - Specific date constraints
WHERE medication_start_date >= diagnosis_date
  AND NOT EXISTS (
      SELECT 1 FROM protective_medications pm
      WHERE pm.start_date <= medication.end_date
        AND pm.end_date >= medication.start_date
  )
```

### ❌ Missing Formulations
```sql
-- WRONG - Only includes tablets
('42356511000001103'),  -- Omeprazole 20mg tablet
```

### ✅ Comprehensive Formulations
```sql
-- CORRECT - Includes all common forms
('42356511000001103'),  -- Omeprazole 20mg tablet
('42356411000001102'),  -- Omeprazole 20mg capsule
('8670711000001107'),   -- Omeprazole 20mg/5ml suspension
```

## Example: Complete Filter Checklist

### Code Collection
- [ ] Filter description and design decisions documented in SQL header
- [ ] All parent/international codes included (for reference)
- [ ] ALL UK dm+d codes collected via SNOMED MCP tool with `uk_extension_only=True`
- [ ] All common formulations included (tablets, capsules, liquids, topicals)
- [ ] All common strengths included (10mg, 20mg, 40mg, etc.)

### Schema & Syntax
- [ ] Uses correct column names from actual schema (e.g., `Dob` not `YearOfBirth`)
- [ ] Uses `DATE_DIFF()` for all date calculations (not CAST on INTERVAL)
- [ ] Uses `{gp_prescriptions}` for medications (not raw GP_Medications)
- [ ] Uses `{gp_events_enriched}` for clinical diagnoses
- [ ] Uses `{patient_view}` for patient demographics (singular, not plural)

### Logic & Output
- [ ] Temporal logic precisely defined (overlaps, >= dates, etc.)
- [ ] Returns: FK_Patient_Link_ID, filter_id, start_date, end_date
- [ ] All date comparisons use proper DuckDB syntax

### Testing & Validation
- [ ] Tested on sample data (returns reasonable number of patients)
- [ ] No SQL errors (check DATE_DIFF syntax, column names)
- [ ] Manual review of 5-10 flagged patients confirms accuracy
- [ ] Expected prevalence documented in comments (typically 0.1% - 2%)

## Resources

- **SNOMED MCP Tool:** Use UK Monolith Edition for medication code searches
  - **Pro tip:** Use `uk_extension_only=True` parameter to filter results to only UK dm+d codes
  - This eliminates manual filtering and speeds up code collection significantly
- **PINCER Literature:** Target prevalence typically 0.1% - 2% of GP population
- **dm+d Documentation:** UK Dictionary of Medicines and Devices
- **Code Pattern:** UK dm+d codes are 13-15 digits containing `1000001`

## Questions?

If you're unsure about:
- **UK dm+d codes:** Search SNOMED MCP with UK Monolith Edition using `uk_extension_only=True`
- **Temporal logic:** Prefer stricter matching (precision over recall)
- **Medication classes:** Include all commonly prescribed formulations and strengths
- **Expected results:** Check literature for PINCER filter prevalence rates
