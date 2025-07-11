from typing import List, Optional
from googleapiclient.discovery import build
from pydantic import BaseModel

from .base import GoogleAPI


class CalendarEvent(BaseModel):
    id: str
    summary: str
    start: str
    end: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None
    html_link: Optional[str] = None


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
