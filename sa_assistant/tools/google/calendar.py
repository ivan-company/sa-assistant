from datetime import datetime, timedelta
from agents import function_tool, RunContextWrapper
from sa_assistant.integrations.google.calendar import GoogleCalendarAPI

from ...context import AssistantContext


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
