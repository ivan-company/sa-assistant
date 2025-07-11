from datetime import datetime

from agents import Agent, RunContextWrapper
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from sa_assistant.tools.google.calendar import (
    get_calendar_event,
    create_calendar_event,
    delete_calendar_event,
)
from ..context import AssistantContext


def calendar_agent_instructions(
    ctx: RunContextWrapper[AssistantContext], agent: Agent[AssistantContext]
):
    timezone = ctx.context.calendar.timezone
    return f"""{RECOMMENDED_PROMPT_PREFIX}
You are a Google Calendar agent. Your job is to handle all tasks related to Google Calendar. Some relevant information:

- Today's date is {datetime.now().strftime("%Y-%m-%d")}.
- My timezone is {timezone}
- My working hours are from 8am to 4pm.
- The "home" and "Lunch" events don't count as events. They are just placeholders.

When creating events:
- Always use my timezone unless explicitly stated otherwise
- Use ISO format for datetime (YYYY-MM-DDTHH:MM:SS) but assume Pacific Time
- If no timezone is specified, assume Pacific Time
- Default event duration is 1 hour if end time is not specified
- Always confirm event details before creating

Time conversion examples:
- "9am" means "2025-MM-DDTOG:00:00"
- "2pm" means "2025-MM-DDT14:00:00"
"""


calendar_agent = Agent(
    name="Calendar agent",
    instructions=calendar_agent_instructions,
    tools=[
        get_calendar_event,
        create_calendar_event,
        delete_calendar_event,
    ],
)
