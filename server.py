from agents import Runner
from mcp.server.fastmcp import FastMCP
from sa_assistant import calendar_agent, jira_agent, slack_agent
from sa_assistant.context import AssistantContext
import yaml

# Create an MCP server
mcp = FastMCP("StackAdapt Assistant")


async def run_agent(agent, request):
    config = yaml.load(open("config.yaml"), Loader=yaml.Loader)

    context = AssistantContext(**config)

    result = await Runner.run(agent, request, context=context)
    return result.final_output


@mcp.tool()
async def calendar(request: str):
    """StackAdapt Calendar agent. In charge of performing all tasks related to calendars
    Args:
        request: The user request that we will need to handle.
    """
    result = await run_agent(calendar_agent, request)

    return result


@mcp.tool()
async def jira(request: str):
    """StackAdapt Jira agent. In charge of performing all tasks related to Jira tickets
    Args:
        request: The user request that we will need to handle.
    """
    result = await run_agent(jira_agent, request)

    return result


@mcp.tool()
async def slack(request: str):
    """StackAdapt Slack agent. In charge of performing all tasks related to Slack messaging
    Args:
        request: The user request that we will need to handle.
    """
    result = await run_agent(slack_agent, request)

    return result

if __name__ == "__main__":
    mcp.run(transport="stdio")
