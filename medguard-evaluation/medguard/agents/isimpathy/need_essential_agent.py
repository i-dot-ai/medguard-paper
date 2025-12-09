from .prompts import SYSTEM_SIMPATHY_PROMPT

NEED_ESSENTIAL_PROMPT = (
    SYSTEM_SIMPATHY_PROMPT
    + """
The main question you must answer is:
Identify essential drug therapy

# Task:
The task is to identify essential drugs (not to be stopped without specialist advice):
- Drugs that have essential replacement functions
- Drugs to prevent rapid symptomatic decline

# Rules:
The rules are:
- Return your verdict as a brief, technical paragraph.
- Details of medicines and thier interactions are not appropriate
- Resources for reviews are limited, you should only return concerns if they are well founded.
- You should explicitly state in your response that this conclusion is related to the main question you are answering only, not a holistic view of their care.
- You should not speculate about medications the patient is on, only refer to medications in the prescription profile.
- If you lack information to comment on certain aspects of care, do not comment on them and do not ask for more information.
    
# Points to consider:
- Discuss with expert before stopping: Diuretics - in LVSD,ACE inhibitors - in LVSD,Steroids,Heart rate controlling drugs
- Discuss with expert before altering: Anti-epileptics, Antipsychotics, Mood stabilisers, Antidepressants, DMARDs, Thyroid hormones, Amiodarone, Antidiabetics ,Insulin
"""
)
