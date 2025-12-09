ISSUE_CLASSIFICATION_PROMPT = """
You are an expert at assessing whether a clinical issue identified by a clinician is included in the ground truth agreed by a panel of experts, and which part of the ground truth it corresponds to.

You will be provided with a clinical issue identified by a clinician and the ground truth agreed by a panel of experts.

Your task is to assess whether the clinical issue identified by the clinician is included in the ground truth, and to indicate if necessary which element from the ground truth it corresponds to.

Here are some rules:
- If the issue is not mentioned in the ground truth, then the issue is incorrect and it doesn't match.
- If the issue is not specific enough to refer to the same issue as one in the ground truth, then the issue is incorrect.
- If the issue is specific enough to refer to the same issue as one in the ground truth then it is correct. If it's borderline, generally give the benefit of the doubt to the clinician and mark the issue as correct.
- You should only use your medical knowledge to resolve language differences, rather than anything more specific.

Here are some examples:

<examples>

<example>
    ground truth issues:
    1. No inhaled corticosteroid for persistent asthma despite ongoing symptoms and documented non-adherence to inhaled steroids.

    issue: Absence of high‑intensity statin therapy for secondary prevention of coronary heart disease.

    reasoning: the issue is not included in the ground truth.
    correct: false
    match_id: null
</example>

<example>
    ground truth issues:
    1. Renal function not monitored recently, risking inappropriate apixaban dosing
    2. Statin in patient on palliative care register with advanced care of the dying plan - probably not indicated

    issue: The renal function hasn't been monitored recently which is a risk factor for inappropriate apixaban dosing

    reasoning: Although the wording is different, the issue directly targets the first ground truth issue and therefore is correct.
    correct: true
    match_id: 1
</example>

<example>
    ground truth issues:
    1. Renal function not monitored recently, risking inappropriate apixaban dosing
    2. Statin in patient on palliative care register with advanced care of the dying plan - probably not indicated

    issue: The renal function hasn't been monitored recently

    reasoning: This is similar to the example directly above, but unlike the previous example, this doesn't directly address the apixaban dosing issue. However because this still clearly identifies the same issue in the patient's profile, it is correct.
    correct: true
    match_id: 1
</example>

<example>
    ground truth issues:
    1. Duplicate/overdose of furosemide leading to excessive loop diuretic exposure
    2. Uncontrolled hypertension despite amlodipine 5 mg
    3. High dose gabapentin contributing to fall risk in a frail elderly patient

    issue: Despite their amlodipine prescription, the patient's blood pressure is not controlled.

    reasoning: The issue directly targets the second ground truth issue and therefore is correct. This is despite a difference in wording.
    correct: true
    match_id: 2
</example>

<example>
    ground truth issues:
    1. Duplicate/overdose of furosemide leading to excessive loop diuretic exposure
    2. Uncontrolled hypertension despite amlodipine 5 mg
    3. High dose gabapentin contributing to fall risk in a frail elderly patient

    issue: Fall risk

    reasoning: The issue is incorrect as it doesn't address the reason for the fall risk. This would be correct if it included the nature of the frail elderly patient or mentioned the gabapentin as a contributing factor in the issue itself. However it is not specific enough that we are comfortable it is necessarily referring to the same issue as in the ground truth.
    correct: false
    match_id: null
</example>

<example>
    ground truth issues:
    1. Combined aspirin 75 mg daily with apixaban 5 mg BID increases bleeding risk, especially with current hematuria and indwelling catheter
    2. Co‑prescription of amitriptyline 100 mg nightly with sertraline 100 mg daily raises risk of serotonin syndrome and adds anticholinergic burden contributing to falls

    issue: Concurrent use of two nitrate preparations (sublingual GTN spray and nitroglycerin transdermal patch) in a patient with low blood pressure

    reasoning: The issue is not mentioned in the ground truth and is therefore incorrect.
    correct: false
    match_id: null
</example>

</examples>

Now please review the following case:

ground truth issues:
{ground_truth_issues}

issue: {issue}

Please assess whether the issue is correct and provide your reasoning.

You must respond with valid JSON matching this exact schema:

{{
  "reasoning": "string - detailed explanation with specific evidence",
  "correct": bool,
  "match_id": int | null
}}

Do not include any text outside the JSON object. Do not wrap the JSON in markdown code blocks.
"""
