from agents import Agent, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from ..models import AssistantContext, AssistantOutput
from .jira import jira_agent, jira_handoff
from .calendar import calendar_agent

triage_agent = Agent[AssistantContext](
    name="Triage agent",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX} "
        "You are a helpful triaging agent. You can use your tools to delegate questions to other appropriate agents."
    ),
    handoffs=[
        handoff(agent=jira_agent, on_handoff=jira_handoff),
        calendar_agent,
    ],
    output_type=AssistantOutput,
)

jira_agent.handoffs.append(triage_agent)
