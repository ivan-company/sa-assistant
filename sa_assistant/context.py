from pydantic import BaseModel, Field
from typing import List


class JiraContext(BaseModel):
    api_key: str = Field(description="The API key for the Jira instance")
    api_email: str = Field(
        description="The email used for creating the API key")
    base_url: str = Field(description="The URL of the Jira instance")
    boards: List[str] = Field(default=[
                              "GROW"], description="List of JIRA boards to analyze for good morning summary")


class CalendarContext(BaseModel):
    timezone: str


class SlackContext(BaseModel):
    api_token: str


class AsanaContext(BaseModel):
    api_token: str
    team_id: str


class AssistantOutput(BaseModel):
    response: str = Field(description="The response to the user's question")


class AssistantContext(BaseModel):
    jira: JiraContext | None = None
    calendar: CalendarContext
    slack: SlackContext
    asana: AsanaContext
    team: List[str] = Field(description="List of your team members")
    managers: List[str] = Field(description="List of your managers")
    openai_api_key: str = Field(description="The OpenAI API key")
    openai_model: str | None = Field(
        default="o4-mini", description="The OpenAI model to use")
