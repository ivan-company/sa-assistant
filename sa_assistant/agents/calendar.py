import os
import json
from pathlib import Path
from datetime import datetime, timedelta

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from agents import Agent, function_tool, RunContextWrapper
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from google_auth_oauthlib.flow import InstalledAppFlow

from ..models import AssistantContext

SCOPES = ['https://www.googleapis.com/auth/calendar']


class CalendarService:
    def __init__(self, client_secrets_file, scopes):
        self.client_secrets_file = client_secrets_file
        self.credentials_file = Path("calendar_credentials.json")
        self.scopes = scopes

    def authenticate_once(self):
        flow = InstalledAppFlow.from_client_secrets_file(
            self.client_secrets_file, self.scopes)
        credentials = flow.run_local_server(port=0)

        self.save_credentials(credentials)

    def save_credentials(self, credentials):
        creds_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

        with open(self.credentials_file, 'w') as f:
            json.dump(creds_data, f)
        os.chmod(self.credentials_file, 0o600)

    def load_credentials(self):
        if not self.credentials_file.exists():
            return None

        with open(self.credentials_file, 'r') as f:
            creds_data = json.load(f)

        return Credentials(**creds_data)

    def get_credentials(self):
        credentials = self.load_credentials()

        if not credentials:
            credentials = self.authenticate_once()

        if credentials.expired:
            credentials.refresh()
            self.save_credentials(credentials)

        return credentials

    def get_service(self):
        credentials = self.get_credentials()
        service = build('calendar', 'v3', credentials=credentials)

        return service


@function_tool
async def get_events(ctx: RunContextWrapper[AssistantContext], date_str: str):
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
    service = CalendarService("calendar_secrets.json", SCOPES).get_service()

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    # Format events for better readability
    formatted_events = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        formatted_event = {
            'id': event.get('id'),
            'summary': event.get('summary', 'No title'),
            'start': start,
            'end': end,
            'description': event.get('description', ''),
            'location': event.get('location', ''),
            'attendees': [attendee.get('email') for attendee in event.get('attendees', [])]
        }
        formatted_events.append(formatted_event)
    return formatted_events


@function_tool
async def create_event(
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
        start_datetime: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
        end_datetime: End time in ISO format (YYYY-MM-DDTHH:MM:SS)
        description: Optional description of the event
        location: Optional location of the event
        attendees: Optional list of email addresses to invite
    """
    calendar_id = 'primary'
    service = CalendarService("calendar_secrets.json", SCOPES).get_service()

    # Build the event object
    event = {
        'summary': summary,
        'description': description,
        'location': location,
        'start': {
            'dateTime': start_datetime,
            'timeZone': 'UTC',  # You might want to make this configurable
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': 'UTC',
        },
    }

    # Add attendees if provided
    if attendees:
        event['attendees'] = [{'email': email} for email in attendees]

    try:
        # Create the event
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()

        # Return formatted response
        return {
            'id': created_event.get('id'),
            'summary': created_event.get('summary'),
            'start': created_event['start'].get('dateTime'),
            'end': created_event['end'].get('dateTime'),
            'html_link': created_event.get('htmlLink'),
            'status': 'created'
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

calendar_agent = Agent(
    name="Calendar agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are a Google Calendar agent. Your job is to handle all tasks related to Google Calendar. Some relevant information:

- Today's date is {datetime.now().strftime("%Y-%m-%d")}.
- My working hours are from 8am to 4pm.
- The "home" and "Lunch" events don't count as events. They are just placeholders.

When creating events:
- Always use ISO format for datetime (YYYY-MM-DDTHH:MM:SS)
- If no timezone is specified, assume EST
- Default event duration is 1 hour if end time is not specified
""",
    tools=[get_events, create_event]
)
