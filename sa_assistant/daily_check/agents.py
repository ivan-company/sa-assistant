from agents import Agent, RunContextWrapper, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from ..context import AssistantContext
from ..jira.agents import get_tickets
from .. import instructions


def jira_daily_checks_instructions(
    ctx: RunContextWrapper[AssistantContext],
    agent: Agent[AssistantContext]
):
    my_team = instructions.my_team(ctx, agent)
    return f"""{RECOMMENDED_PROMPT_PREFIX}
Note: {my_team}
Your task is to create a report from the data extracted from Jira. First you will get all the tickets for my team for the current sprint. For each one of the tickets, I want you to return the following information:

- ticket name
- assignee
- if the description is meaningful (this means, no short descriptions, no copy/paste from the summary)
- Check it has story points defined
- Jira URL link to the ticket
    """


jira_daily_checks_agent = Agent[AssistantContext](
    name="Jira Daily Checks agent",
    instructions=jira_daily_checks_instructions,
    tools=[get_tickets]
)


daily_checks_agent = Agent[AssistantContext](
    name="Daily checks agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are an agent specialized in performing daily checks on your team. You will build a report based on the results of your delegated agents:

- For The Jira daily check, you'll ask your Jira daily check agent

""",
    handoffs=[handoff(jira_daily_checks_agent, on_handoff=lambda ctx: print(
        "handing off to the Jira Daily checks agent"))]
)
