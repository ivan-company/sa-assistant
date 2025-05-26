from agents import Agent, handoff, RunContextWrapper
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from ..context import AssistantContext, AssistantOutput
from ..jira.agent import jira_agent, jira_handoff
from ..calendar.agent import calendar_agent
from ..slack.agent import slack_agent
from ..daily_check.agent import daily_checks_agent


async def daily_checks_agent_handoff(ctx: RunContextWrapper[AssistantContext]):
    print("Handing off work to the daily checks agent")

triage_agent = Agent[AssistantContext](
    name="Triage agent",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX} "
        "You are a helpful triaging agent. You can use your tools to delegate questions to other appropriate agents."
    ),
    handoffs=[
        handoff(daily_checks_agent, on_handoff=daily_checks_agent_handoff),
        handoff(agent=jira_agent, on_handoff=jira_handoff),
        calendar_agent,
        slack_agent,
    ],
    output_type=AssistantOutput,
)

jira_agent.handoffs.append(triage_agent)
