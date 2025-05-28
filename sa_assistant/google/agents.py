from datetime import datetime, timedelta

from agents import Agent, function_tool, RunContextWrapper
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from ..context import AssistantContext
from .api import GoogleCalendarAPI


@function_tool
async def get_calendar_event(ctx: RunContextWrapper[AssistantContext], date_str: str):
    """Fetch the calendar information.

    Args:
    date: string representing the date the user wants to check. If not provided, it will be used today's date. Its format is YYYY-MM-DD.
    """
    date = datetime.strptime(date_str, "%Y-%m-%d")
    days_ahead = 1
    max_results = 10
    calendar_id = 'primary'
    time_min = date.isoformat() + 'Z'
    time_max = (date + timedelta(days=days_ahead)).isoformat() + 'Z'
    try:
        events = GoogleCalendarAPI().get_events(
            calendar_id,
            time_min=time_min,
            time_max=time_max,
            max_results=max_results,
            order_by='startTime'
        )
    except Exception as e:
        print(e)
    return events


@function_tool
async def create_calendar_event(
    ctx: RunContextWrapper[AssistantContext],
    summary: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    location: str = "",
    attendees: list[str] = None
):
    """Create a new event in the calendar.

    Args:
        summary: The title/summary of the event
        start_datetime: Start time in ISO format (YYYY-MM-DDTHH:MM:SS) - assumed to be in Pacific Time
        end_datetime: End time in ISO format (YYYY-MM-DDTHH:MM:SS) - assumed to be in Pacific Time
        description: Optional description of the event
        location: Optional location of the event
        attendees: Optional list of email addresses to invite
    """
    calendar_id = 'primary'

    # Build the event object
    event = {
        'summary': summary,
        'description': description,
        'location': location,
        'start': {
            'dateTime': start_datetime,
            'timeZone': 'America/Vancouver',  # Pacific Time
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': 'America/Vancouver',  # Pacific Time
        },
    }

    # Add attendees if provided
    if attendees:
        event['attendees'] = [{'email': email} for email in attendees]

    try:
        return GoogleCalendarAPI().create_event(calendar_id, event)
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


@function_tool
async def delete_calendar_event(
    ctx: RunContextWrapper[AssistantContext],
    event_id: str
):
    """Delete an event from the calendar.

    Args:
        event_id: The ID of the event to delete
    """
    try:
        GoogleCalendarAPI().delete_event(event_id, 'primary')
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'event_id': event_id
        }


def calendar_agent_instructions(ctx: RunContextWrapper[AssistantContext], agent: Agent[AssistantContext]):
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
    ]
)
