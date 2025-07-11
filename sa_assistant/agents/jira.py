import json
from typing import Dict, Any
from agents import Agent, function_tool, RunContextWrapper
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from jira import JIRA
from dotenv import load_dotenv
import openai
from sa_assistant.tools.jira import get_tickets
from ..context import AssistantContext, JiraContext

load_dotenv()


async def analyze_ticket_content_with_ai(
    content: str, openai_api_key: str, model: str
) -> Dict[str, Any]:
    """
    Use AI to semantically analyze ticket content for blockers and decisions.
    Uses the model specified in config.yaml.
    """
    print(f"Analyzing ticket content with model: {model}")
    client = openai.AsyncOpenAI(api_key=openai_api_key)

    prompt = f"""
    Analyze the following JIRA ticket content (including description and comments) and determine:

    1. Does this content indicate a BLOCKER? (Something that prevents progress, creates dependencies, or requires external resolution)
    2. Does this content indicate a TECHNICAL/PRODUCT DECISION that needs to be made? (Architecture choices, product direction, technical approach, etc.)

    For each category that applies, provide:
    - A confidence score (0-100)
    - A brief explanation of why it qualifies
    - Key phrases that support your assessment

    Content to analyze:
    {content}

    Respond in JSON format:
    {{
        "blocker": {{
            "detected": true/false,
            "confidence": 0-100,
            "explanation": "brief explanation",
            "key_phrases": ["phrase1", "phrase2"]
        }},
        "decision": {{
            "detected": true/false,
            "confidence": 0-100,
            "explanation": "brief explanation",
            "key_phrases": ["phrase1", "phrase2"]
        }}
    }}
    """

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert at analyzing software development tickets to identify blockers and decision points."
                        " Be precise and only flag items with high confidence."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"Error in AI analysis: {e}")
        return {
            "blocker": {
                "detected": False,
                "confidence": 0,
                "explanation": "AI analysis failed",
                "key_phrases": [],
            },
            "decision": {
                "detected": False,
                "confidence": 0,
                "explanation": "AI analysis failed",
                "key_phrases": [],
            },
        }


@function_tool
async def good_morning(ctx: RunContextWrapper[AssistantContext]) -> Dict[str, Any]:
    """
    Good morning function that analyzes tickets across configured JIRA boards.
    Identifies blockers/decisions needing EM attention.
    Board list is configured in config.yaml under jira.boards.
    Uses AI-powered semantic analysis to detect blockers and decisions.

    Scope: Only analyzes tickets in the current sprint (open sprints).
    """
    # Get boards from configuration
    boards = (
        ctx.context.jira.boards
        if ctx.context.jira and ctx.context.jira.boards
        else ["CRE"]
    )
    print(f"Running good morning analysis for boards: {boards}")

    try:
        jira = JIRA(
            server=ctx.context.jira.base_url,
            basic_auth=(ctx.context.jira.api_email, ctx.context.jira.api_key),
        )
    except Exception as e:
        print(f"Error connecting to JIRA: {e}")
        return {"error": "Failed to connect to JIRA"}

    results = {
        "blockers_and_decisions": [],
        "summary": {
            "total_tickets_analyzed": 0,
            "potential_blockers": 0,
            "decision_items": 0,
            "boards_analyzed": boards,
        },
    }

    for board in boards:
        print(f"Analyzing board: {board}")

        # Get active tickets from the board (not Done/Closed) in current sprint only, excluding Test and Task types
        jql_query = f'project = "{board}" AND status NOT IN ("DONE", "QA REVIEW", "READY TO MERGE", "WONT DO") AND type NOT IN ("Test", "Task") AND Sprint in openSprints() ORDER BY updated DESC'
        print(f"JQL query: {jql_query}")

        try:
            issues = jira.search_issues(jql_query, expand="comments", maxResults=50)

            for issue in issues:
                print(f"Analyzing issue: {issue.key}")
                results["summary"]["total_tickets_analyzed"] += 1

                # Get full issue details including comments
                full_issue = jira.issue(issue.key, expand="comments")

                # Combine all text content for analysis
                all_text = []
                all_text.append(full_issue.fields.summary or "")
                all_text.append(full_issue.fields.description or "")

                # Get comments
                if hasattr(full_issue.fields, "comment") and full_issue.fields.comment:
                    for comment in full_issue.fields.comment.comments:
                        comment_body = comment.body or ""
                        all_text.append(comment_body)

                combined_text = " ".join(all_text)

                # Use AI to analyze for blockers and decisions
                if (
                    len(combined_text.strip()) > 50
                ):  # Only analyze if there's substantial content
                    ai_analysis = await analyze_ticket_content_with_ai(
                        combined_text,
                        ctx.context.openai_api_key,
                        ctx.context.openai_model or "gpt-4o-mini",
                    )

                    blocker_detected = ai_analysis.get("blocker", {}).get(
                        "detected", False
                    )
                    blocker_confidence = ai_analysis.get("blocker", {}).get(
                        "confidence", 0
                    )
                    decision_detected = ai_analysis.get("decision", {}).get(
                        "detected", False
                    )
                    decision_confidence = ai_analysis.get("decision", {}).get(
                        "confidence", 0
                    )

                    # Only flag items with high confidence (>70)
                    if (blocker_detected and blocker_confidence > 70) or (
                        decision_detected and decision_confidence > 70
                    ):
                        item_type = []
                        analysis_details = {}

                        if blocker_detected and blocker_confidence > 70:
                            item_type.append("blocker")
                            results["summary"]["potential_blockers"] += 1
                            analysis_details["blocker"] = ai_analysis["blocker"]

                        if decision_detected and decision_confidence > 70:
                            item_type.append("decision")
                            results["summary"]["decision_items"] += 1
                            analysis_details["decision"] = ai_analysis["decision"]

                        results["blockers_and_decisions"].append(
                            {
                                "key": full_issue.key,
                                "summary": full_issue.fields.summary,
                                "status": full_issue.fields.status.name,
                                "assignee": (
                                    full_issue.fields.assignee.displayName
                                    if full_issue.fields.assignee
                                    else "Unassigned"
                                ),
                                "board": board,
                                "type": item_type,
                                "ai_analysis": analysis_details,
                                "priority": (
                                    full_issue.fields.priority.name
                                    if hasattr(full_issue.fields, "priority")
                                    and full_issue.fields.priority
                                    else "Unknown"
                                ),
                                "url": f"{ctx.context.jira.base_url}/browse/{full_issue.key}",
                            }
                        )

        except Exception as e:
            print(f"Error analyzing board {board}: {e}")
            continue

    return results


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
- If not specified, you will retrieve the tickets for the current sprint.

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
    tools=[get_tickets, good_morning],
    handoffs=[jql_agent],
)


async def jira_handoff(ctx: RunContextWrapper[AssistantContext]):
    print("Handing off work to Jira agent")
