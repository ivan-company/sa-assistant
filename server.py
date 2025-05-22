from agents import Runner
from mcp.server.fastmcp import FastMCP
from sa_assistant.agents.triage import triage_agent
from sa_assistant.models import AssistantContext

# Create an MCP server
mcp = FastMCP("Demo")


# Add an addition tool
@mcp.tool()
async def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.tool()
async def sa_assistant(request: str):
    """StackAdapt AI assistant. It's in charge of solving all types of requests in regards of StackAdapt

    Args:
        request: The user request that we will need to handle.
    """

    context = AssistantContext()

    result = await Runner.run(triage_agent, request, context=context)
    return result.final_output


if __name__ == "__main__":
    mcp.run(transport="stdio")
