from agents import Runner
from mcp.server.fastmcp import FastMCP
from sa_assistant.agents.triage import triage_agent
from sa_assistant.models import AssistantContext
import yaml

# Create an MCP server
mcp = FastMCP("Demo")


@mcp.tool()
async def sa_assistant(request: str):
    """StackAdapt AI assistant. It's in charge of solving all types of requests in regards of StackAdapt

    Args:
        request: The user request that we will need to handle.
    """

    config = yaml.load(open("config.yaml"), Loader=yaml.Loader)

    context = AssistantContext(**config)

    result = await Runner.run(triage_agent, request, context=context)
    return result.final_output


if __name__ == "__main__":
    mcp.run(transport="stdio")
