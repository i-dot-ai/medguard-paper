from inspect_ai.agent import Agent, AgentState, agent
from inspect_ai.model import ChatMessageSystem, get_model

FLAGGING_REVIEW_PROMPT = r"""
# Task
You are an experienced pharamacist. Please decide whether the patients prescription profile should be flagged for review by a human clinician.
Each review takes up considerable time and resources, so only flag the prescription profile you are confident have significant issues and that you have strong evidence to support your decision.
Please do not flag the prescription profiles based on assumptions.
When considering interaction in prescription profiles, only include medications that are likely to have been taken at the same time, use the timestamps to inform your answer.
The report should have the following format where the reasoning, flag and severity are all in XML tags:

# Format
<reasoning>Reasoning body</reasoning>
<flag>Yes or No</flag>
<severity>No Harm, Minor, Moderate, Serious or Severe</severity>

Where:
- Reasoning body is a detailed but concise explanation of why you have selected the output. This should
be evidence based and leave little for interpretation.
- Flag is either "Yes" or "No" and details whether the prescription profile should be reviewed.
Only Serious and Severe cases should be flagged for review. Do not include any other words in this response.
- Severity is either :"No Harm", "Minor", "Moderate", "Serious" and "Severe". This is based on the
Harm Associated with Medication Errors Classifcation (HAMEC) scale. Full details of the scale can be found
below. Do not include any other words in this response.


# Harm Associated with Medication Errors Classifcation (HAMEC) scale:
* No harm - No potential for patient harm, nor any change in patient monitoring, level or length of care required
* Minor - There was potential for minor, non-life threatening, temporary harm that may or may not require eforts
to assess for a change in a patient’s condition such as monitoring. These eforts may or may not have potentially
caused minimal increase in length of care (<1 day)
* Moderate - There was potential for minor, non-life threatening, temporary harm that would require eforts to assess
for a change in a patient’s condition such as monitoring, and additional low-level change in a patient’s level of care
such as a blood test. Any potential increase in the length of care is likely to be minimal (<1 day)
* Serious - There was potential for major, non-life threatening, temporary harm, or minor permanent harm that would
require a high level of care such as the administration of an antidote. An increase in the length of care of≥1 day is
expected
* Severe - There was potential for life-threatening or mortal harm, or major permanent harm that would require a high
level of care such as the administration of an antidote or transfer to intensive care. A substantial increase in the
length of care of>1 day is expected
"""


@agent
def patient_flagger() -> Agent:
    async def execute(state: AgentState) -> AgentState:
        state.messages.append(ChatMessageSystem(content=FLAGGING_REVIEW_PROMPT))

        state.output = await get_model().generate(input=state.messages)

        state.messages.append(state.output.message)

        return state

    return execute
