from datetime import datetime

from agents import Agent, RunContextWrapper, function_tool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
import pytz

from ..context import AssistantContext
from ..asana.api import AsanaAPI
from ..google.api import GoogleCalendarAPI
from .models import DailyCheckOutput, DailyCheckEventType, DailyCheckCalendarEvent
from ..utils import name_to_email


def daily_calendar_check_instructions(
    ctx: RunContextWrapper[AssistantContext], agent: Agent[AssistantContext]
):
    return (
        f"""{RECOMMENDED_PROMPT_PREFIX}
You are an agent that summarizes the user's calendar and checks for 1:1 meetings for a specific day.
Today's date is {datetime.now().strftime("%Y-%m-%d")}.
If the user asks for a daily calendar check for a specific day (e.g., 'next Wednesday', 'in two days', 'tomorrow', or a specific date), always convert that to a YYYY-MM-DD date string and include it in the request parameter when calling the tool. If the user does not specify a date, use today's date.
For each 1:1 (only you and one other @stackadapt.com attendee), check if there is an Asana project named 'FirstName & Ivan'.
If so, list all unfinished tasks for that project.
"""
    )


@function_tool
async def daily_calendar_check(ctx: RunContextWrapper[AssistantContext], requested_date: str = "") -> DailyCheckOutput:
    # Try to extract a date from the user prompt
    result = DailyCheckOutput(calendar_events=[])

    manager_emails = [name_to_email(m) for m in ctx.context.managers]

    user_tz_str = getattr(ctx.context.calendar, 'timezone', 'UTC')
    user_tz = pytz.timezone(user_tz_str)
    now = datetime.now(user_tz)
    try:
        date_obj = user_tz.localize(
            datetime.strptime(requested_date, "%Y-%m-%d"))
    except ValueError:
        date_obj = now

    calendar_api = GoogleCalendarAPI()
    asana_api = AsanaAPI(ctx.context.asana.api_token,
                         ctx.context.asana.team_id)

    calendar_events = calendar_api.get_events(
        calendar_id='primary',
        time_min=(date_obj.replace(hour=0, minute=0,
                  second=0, microsecond=0).isoformat()),
        time_max=(date_obj.replace(hour=23, minute=59,
                  second=59, microsecond=999999).isoformat()),
        max_results=20,
        order_by='startTime'
    )
    for event in calendar_events:
        asana_tasks = []
        # Only consider events with attendees
        if not event.attendees:
            continue
        # Find the other attendee
        attendees = [
            a for a in event.attendees
            if a and a not in manager_emails
        ]
        if len(attendees) == 1:
            event_type = DailyCheckEventType.ONE_TO_ONE
            print(f"One to one with {attendees[0]}")
            projects = asana_api.get_projects_with_users([attendees[0]])
            for project in projects:
                print(f"Project: {project.name}")
                tasks = asana_api.get_tasks_by_project(project.gid)
                asana_tasks.extend(tasks)
        else:
            event_type = DailyCheckEventType.TEAM_MEETING

        result.calendar_events.append(
            DailyCheckCalendarEvent(
                event=event,
                event_type=event_type,
                asana_tasks=asana_tasks
            )
        )

    return result


daily_calendar_check_agent = Agent[
    AssistantContext](
    name="Daily Calendar Check agent",
    instructions=daily_calendar_check_instructions,
    tools=[daily_calendar_check],
    output_type=DailyCheckOutput
)
