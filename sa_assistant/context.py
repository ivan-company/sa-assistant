from pydantic import BaseModel, Field
from typing import List


class JiraContext(BaseModel):
    api_key: str = Field(description="The API key for the Jira instance")
    api_email: str = Field(
        description="The email used for creating the API key")
    base_url: str = Field(description="The URL of the Jira instance")


class CalendarContext(BaseModel):
    timezone: str


class SlackContext(BaseModel):
    api_token: str


class AsanaContext(BaseModel):
    api_token: str
    team_id: str


class AssistantOutput(BaseModel):
    response: str = Field(description="The response to the user's question")


class TicketInfo(BaseModel):
    key: str = Field(description="The ticket key (e.g., PROJ-123)")
    summary: str = Field(description="The ticket summary")
    status: str = Field(description="Current status of the ticket")
    assignee: str = Field(
        description="Name of the person assigned to the ticket")
    story_points: float | None = Field(
        default=None, description="Story points for the ticket")


class AssistantContext(BaseModel):
    jira: JiraContext | None = None
    calendar: CalendarContext
    slack: SlackContext
    asana: AsanaContext
    team: List[str] = Field(description="List of your team members")
    managers: List[str] = Field(description="List of your managers")
