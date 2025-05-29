from datetime import datetime, timedelta

from agents import Agent, function_tool, RunContextWrapper
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from ..context import AssistantContext
from .api import GoogleCalendarAPI, GoogleDriveAPI


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


@function_tool
async def create_drive_file(
    ctx: RunContextWrapper[AssistantContext],
    file_name: str,
    file_content: str
):
    """Create a new file in the drive.

    Args:
        file_name: The name of the file
        file_content: The content of the file
    """
    return GoogleDriveAPI().create_file(file_name, file_content)


@function_tool
async def delete_drive_file(
    ctx: RunContextWrapper[AssistantContext],
    file_id: str
):
    """Delete a file from the drive.

    Args:
        file_id: The ID of the file to delete
    """
    return GoogleDriveAPI().delete_file(file_id)


@function_tool
async def list_files_in_path(
    ctx: RunContextWrapper[AssistantContext],
    path: str
):
    """List files in the drive.

    Args:
        path: The path to the folder to list files in
    """
    return GoogleDriveAPI().list_files_in_path(path)


@function_tool
async def read_drive_file_by_path(
    ctx: RunContextWrapper[AssistantContext],
    file_path: str
):
    """Read a file from the drive.

    Args:
        file_path: The path to the file to read
    """
    try:
        return GoogleDriveAPI().download_file_by_path(file_path)
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'file_path': file_path
        }


def drive_agent_instructions(ctx: RunContextWrapper[AssistantContext], agent: Agent[AssistantContext]):
    timezone = ctx.context.calendar.timezone
    return f"""{RECOMMENDED_PROMPT_PREFIX}
You are a Google Drive agent. Your job is to handle all tasks related to Google Drive, including:
- Creating, reading, updating, and deleting files and folders
- Listing files and folders in any directory
- Moving and renaming files or folders
- Sharing files or folders with others
- Searching for files or folders by name

Some relevant information:
- Today's date is {datetime.now().strftime("%Y-%m-%d")}.
- My timezone is {timezone}

**Guidelines:**
- Always confirm file/folder names and paths with the user if there is ambiguity.
- If you encounter an error or cannot find a file/folder, inform the user and suggest next steps.
- If you are unsure about a request, ask the user for clarification.

**Examples:**
- "Create a file named 'report.txt' in the 'Projects' folder."
- "List all files in the 'Invoices/2024' folder."
- "Share 'presentation.pdf' with alice@example.com."
"""


drive_agent = Agent(
    name="Drive agent",
    instructions=drive_agent_instructions,
    tools=[
        create_drive_file,
        delete_drive_file,
        list_files_in_path,
        read_drive_file_by_path,
    ]
)
