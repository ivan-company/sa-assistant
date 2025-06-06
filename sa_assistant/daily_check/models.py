from typing import List
from enum import Enum
from pydantic import BaseModel
from ..google.models import CalendarEvent
from ..asana.models import AsanaTask


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
