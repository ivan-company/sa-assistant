from typing import Optional, List
from pydantic import BaseModel


class CalendarEvent(BaseModel):
    id: str
    summary: str
    start: str
    end: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None
    html_link: Optional[str] = None
