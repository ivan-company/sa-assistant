from agents import Agent, RunContextWrapper, function_tool
from ..models import AssistantContext
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


@function_tool
def send_message(ctx: RunContextWrapper[AssistantContext], message: str):
    """Sends a message to Slack

    Args:
        message: The content of the message
    """
    print("Slack agent")
    slack_token = ctx.context.slack.api_token
    client = WebClient(token=slack_token)
    try:
        print(f"Preparing to send the message '{message}'")
        response = client.chat_postMessage(
            channel="U08AZ7TFCP6",
            text=message
        )
    except SlackApiError as e:
        print("error", e)
        # You will get a SlackApiError if "ok" is False
        # str like 'invalid_auth', 'channel_not_found'
        assert e.response["error"]


slack_agent = Agent(
    name="Slack agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are an agent specialized in operating with Slack.
""",
    tools=[
        send_message
    ]
)
