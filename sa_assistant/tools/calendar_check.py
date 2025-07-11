from datetime import datetime
from typing import List
from enum import Enum
from pydantic import BaseModel
import pytz

from agents import RunContextWrapper, function_tool
from sa_assistant.context import AssistantContext
from sa_assistant.integrations.asana import AsanaAPI
from sa_assistant.integrations.google.calendar import GoogleCalendarAPI
from sa_assistant.utils import name_to_email


from sa_assistant.integrations.google.calendar import CalendarEvent
from sa_assistant.integrations.asana import AsanaTask


class DailyCheckEventType(Enum):
    """
    The type of event for the daily check.
    """
    ONE_TO_ONE = "one_to_one"
    TEAM_MEETING = "team_meeting"
    OTHER = "other"


class DailyCheckCalendarEvent(BaseModel):
    """
    A calendar event for the daily check.
    """
    event: CalendarEvent
    asana_tasks: List[AsanaTask]
    event_type: DailyCheckEventType


class DailyCheckOutput(BaseModel):
    """
    Output for the daily calendar check.
    """
    calendar_events: List[DailyCheckCalendarEvent]


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
            projects = asana_api.get_projects_with_users([attendees[0]])
            for project in projects:
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
