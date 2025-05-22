from pydantic import BaseModel, Field


class JiraContext(BaseModel):
    jira_api_key: str = Field(description="The API key for the Jira instance")
    jira_instance_url: str = Field(description="The URL of the Jira instance")


class AssistantContext(BaseModel):
    jira: JiraContext | None = None


class AssistantOutput(BaseModel):
    response: str = Field(description="The response to the user's question")


class TicketInfo(BaseModel):
    key: str = Field(description="The ticket key (e.g., PROJ-123)")
    summary: str = Field(description="The ticket summary")
    status: str = Field(description="Current status of the ticket")
    assignee: str = Field(description="Name of the person assigned to the ticket")
