from medguard.tools import (
    get_bnf_drug_profile,
)

from .prompts import SYSTEM_SIMPATHY_PROMPT

PATIENT_CENTRED_PROMPT = (
    SYSTEM_SIMPATHY_PROMPT
    + """
The main question you must answer is:
Is the patient willing and able to take drug therapy as intended?

# Task:
The task you must fulfill to answer this question is to Ensure drug therapy changes are tailored to patient preferences:
- Is the medication in a form the patient can take?
- Is the dosing schedule convenient?
- Consider what assistance the patient might have and when this is available
- Is the patient able to take medicines as intended?

# Rules:
The rules are:
- Return your verdict as a brief, technical paragraph.
- Resources for reviews are limited, you should only return concerns if they are well founded.
- You should explicitly state in your response that this conclusion is related to the main question you are answering only, not a holistic view of their care.
- You should not speculate about medications the patient is on, only refer to medications in the prescription profile.
- If you lack information to comment on certain aspects of care, do not comment on them and do not ask for more information.

# Points to consider:
- Check Self-Administration (Cognitive):  Warfarin/DOACs, Anticipatory care meds e.g. COPD, Analgesics, Methotrexate, Tablet Burden
- Check Self-Administration (Technical): Inhalers, Eye Drops
"""
)

patient_centred_agent_tools = [
    get_bnf_drug_profile(),
]
