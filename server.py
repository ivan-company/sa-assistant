from agents import Runner, RunConfig
from mcp.server.fastmcp import FastMCP
from sa_assistant import calendar_agent, jira_agent, slack_agent, drive_agent, daily_calendar_check_agent
from sa_assistant.context import AssistantContext
from sa_assistant.utils import load_config_and_setup_env

# Create an MCP server
mcp = FastMCP("StackAdapt Assistant")


async def run_agent(agent, request):
    config, context = load_config_and_setup_env()
    
    # Create RunConfig with the model from context
    run_config = RunConfig(model=context.openai_model)

    result = await Runner.run(agent, request, context=context, run_config=run_config)
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


@mcp.tool()
async def drive(request: str):
    """StackAdapt Drive agent. In charge of performing all tasks related to Google Drive
    Args:
        request: The user request that we will need to handle.
    """
    result = await run_agent(drive_agent, request)

    return result


@mcp.tool()
async def daily_calendar_check(request: str):
    """StackAdapt Daily calendar check agent. In charge of performing all tasks related to daily calendar checks
    Args:
        request: The user request that we will need to handle.
    """
    result = await run_agent(daily_calendar_check_agent, request)

    return result


if __name__ == "__main__":
    mcp.run(transport="stdio")
