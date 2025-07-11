from agents import function_tool, RunContextWrapper
from jira import JIRA
from pydantic import BaseModel, Field

from ..context import AssistantContext


class TicketInfo(BaseModel):
    key: str = Field(description="The ticket key (e.g., PROJ-123)")
    summary: str = Field(description="The ticket summary")
    status: str = Field(description="Current status of the ticket")
    assignee: str = Field(
        description="Name of the person assigned to the ticket")
    story_points: float | None = Field(
        default=None, description="Story points for the ticket")


@function_tool
async def get_tickets(
    ctx: RunContextWrapper[AssistantContext], jql: str
) -> list[TicketInfo]:
    """Get tickets based on a JQL query."""
    try:
        jira = JIRA(
            server=ctx.context.jira.base_url,
            basic_auth=(ctx.context.jira.api_email,
                        ctx.context.jira.api_key),
        )
    except Exception as e:
        print(e)
        return []

    # Get tickets based on the JQL query
    issues = jira.search_issues(jql)

    data = [
        TicketInfo(
            key=issue.key,
            summary=issue.fields.summary,
            status=issue.fields.status.name,
            assignee=(
                issue.fields.assignee.displayName
                if issue.fields.assignee
                else "Unassigned"
            ),
            story_points=getattr(issue.fields, "customfield_10708", None),
        )
        for issue in issues
    ]

    return data
