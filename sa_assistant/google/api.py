import os
import json
from pathlib import Path
from typing import List

from googleapiclient.discovery import build, Resource
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from .models import CalendarEvent


SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive',
]


class GoogleAPI:
    def __init__(self):
        self.client_secrets_file = Path("google_secrets.json")
        self.credentials_file = Path("google_credentials.json")

    def authenticate_once(self):
        flow = InstalledAppFlow.from_client_secrets_file(
            self.client_secrets_file, SCOPES)
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
        raise NotImplementedError


class GoogleCalendarAPI(GoogleAPI):
    def get_service(self):
        return build('calendar', 'v3', credentials=self.get_credentials())

    def delete_event(self, event_id: str, calendar_id='primary') -> CalendarEvent:
        service = self.get_service()
        event = service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()

        event_summary = event.get('summary', 'No title')
        event_start = event['start'].get(
            'dateTime', event['start'].get('date'))

        # Delete the event
        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()

        return CalendarEvent(
            id=event_id,
            summary=event_summary,
            start=event_start,
        )

    def get_events(self, calendar_id: str, time_min: str, time_max: str, max_results: int, order_by: str) -> List[CalendarEvent]:
        print("getting events")
        events_result = self.get_service().events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy=order_by
        ).execute()

        events = events_result.get('items', [])

        # Format events for better readability
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            formatted_event = CalendarEvent(
                id=event.get('id'),
                summary=event.get('summary', 'No title'),
                start=start,
                end=end,
                description=event.get('description', ''),
                location=event.get('location', ''),
                attendees=[attendee.get('email')
                           for attendee in event.get('attendees', [])]
            )
            formatted_events.append(formatted_event)

        return formatted_events

    def create_event(self, calendar_id, event_body) -> CalendarEvent:
        created_event = self.get_service().events().insert(
            calendarId=calendar_id,
            body=event_body
        ).execute()

        return CalendarEvent(
            id=created_event.get('id'),
            summary=created_event.get('summary'),
            start=created_event['start'].get('dateTime'),
            end=created_event['end'].get('dateTime'),
            html_link=created_event.get('htmlLink'),
        )


class GoogleDriveAPI(GoogleAPI):

    def get_service(self) -> Resource:
        return build('drive', 'v3', credentials=self.get_credentials())
