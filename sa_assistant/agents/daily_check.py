from datetime import datetime

from agents import Agent, RunContextWrapper
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from sa_assistant.context import AssistantContext
from sa_assistant.tools.calendar_check import daily_calendar_check, DailyCheckOutput


def daily_calendar_check_instructions(
    ctx: RunContextWrapper[AssistantContext], agent: Agent[AssistantContext]
):
    return f"""{RECOMMENDED_PROMPT_PREFIX}
You are an agent that summarizes the user's calendar and checks for 1:1 meetings for a specific day.
Today's date is {datetime.now().strftime("%Y-%m-%d")}.
If the user asks for a daily calendar check for a specific day (e.g., 'next Wednesday', 'in two days', 'tomorrow', or a specific date), always convert that to a YYYY-MM-DD date string and include it in the request parameter when calling the tool. If the user does not specify a date, use today's date.
For each 1:1 (only you and one other @stackadapt.com attendee), check if there is an Asana project named 'FirstName & Ivan'.
If so, list all unfinished tasks for that project.
"""


daily_calendar_check_agent = Agent[AssistantContext](
    name="Daily Calendar Check agent",
    instructions=daily_calendar_check_instructions,
    tools=[daily_calendar_check],
    output_type=DailyCheckOutput,
)
