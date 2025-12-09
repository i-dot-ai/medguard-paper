from inspect_ai.agent import Agent, agent, react

from medguard.tools import (
    get_bnf_drug_interactions,
    get_bnf_drug_profile,
)

from .prompt import REACT_PROMPT


@agent
def react_agent(attempts: int = 1) -> Agent:
    return react(
        description="Expert at flagging patients with inappropriate polypharmacy",
        prompt=REACT_PROMPT,
        tools=[get_bnf_drug_profile(), get_bnf_drug_interactions()],
        attempts=attempts,
    )
