import os

from agents import Agent, function_tool, RunContextWrapper
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from jira import JIRA
from dotenv import load_dotenv

from ..models import AssistantContext, TicketInfo, JiraContext

load_dotenv()


@function_tool
async def get_tickets(
    ctx: RunContextWrapper[AssistantContext], jql: str
) -> list[TicketInfo]:
    """Get tickets based on a JQL query."""
    print("Getting tickets with query:", jql)
    try:
        jira = JIRA(
            server=ctx.context.jira.jira_instance_url,
            basic_auth=(os.getenv("JIRA_API_EMAIL"), ctx.context.jira.jira_api_key),
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
        )
        for issue in issues
    ]

    return data


jql_agent = Agent[AssistantContext](
    name="JQL Translation agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are a specialist in translating natural language requests into JQL queries.
Your job is to understand what the user wants and create an appropriate JQL query.

You have deep knowledge of JQL syntax and can handle complex queries. Here's what you can do:

Common JQL fields:
- assignee: who the ticket is assigned to
- reporter: who created the ticket
- status: current status (e.g., 'In Progress', 'Done', 'Blocked')
- priority: ticket priority (e.g., 'High', 'Medium', 'Low')
- created: when the ticket was created
- updated: when the ticket was last updated
- due: when the ticket is due
- project: the project the ticket belongs to
- type: the type of ticket (e.g., 'Bug', 'Task', 'Story')
- labels: tags associated with the ticket
- description: ticket description
- summary: ticket title

Common operators:
- =, != : equals, not equals
- >, <, >=, <= : greater than, less than, etc.
- IN, NOT IN : in a list of values
- WAS, WAS IN, WAS NOT, WAS NOT IN : historical values
- CHANGED, CHANGED FROM, CHANGED TO : changes in field values
- AFTER, BEFORE, ON, DURING : date comparisons
- ORDER BY : sort results

- When the user asks for their team. They usually talk about Devon Mack, Cynthia Tsoi and Larry Liu

When you are asked about a specific user, you can translate it to their email address by using the following syntax:
- "John Doe" -> "john.doe@stackadapt.com"
- "Jane Smith" -> "jane.smith@stackadapt.com"

Examples:
- "my tickets" -> "assignee = currentUser()"
- "tickets created last week" -> "created >= -7d"
- "high priority bugs" -> "priority = High AND type = Bug"
- "tickets updated today" -> "updated >= startOfDay()"

When you receive a request:
1. Understand what the user wants
2. Generate the appropriate JQL query
3. Use the get_tickets function with your generated query
4. Explain what the query will return

Always provide a clear explanation of what the query will return.
""",
    tools=[get_tickets],
)


jira_agent = Agent[JiraContext](
    name="Ticketing agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are a helpful assistant that can interact with everything related to tickets.
First, use the JQL translation agent to convert the user's request into a JQL query.
Then, use the get_tickets function with that query to fetch the relevant tickets.
If the customer asks a question that is not related to tickets, transfer back to the triage agent.
""",
    tools=[get_tickets],
    handoffs=[jql_agent],
)


async def jira_handoff(ctx: RunContextWrapper[AssistantContext]):
    print("Handing off work to Jira agent")
    ctx.context.jira = JiraContext(
        jira_api_key=os.getenv("JIRA_API_KEY"),
        jira_instance_url=os.getenv("JIRA_BASE_URL"),
    )
