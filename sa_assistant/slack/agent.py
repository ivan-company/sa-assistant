from agents import Agent, RunContextWrapper, function_tool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from ..context import AssistantContext
from . import db
from . import models
from .api import SlackAPI


def get_conversation(slack_token: str, conversation_id: str) -> models.SlackConversation:
    api = SlackAPI(slack_token)
    result = None
    conversation_name = conversation_id[1:]
    if conversation_id.startswith("#"):
        result = db.fetch_channel(channel_name=conversation_name)
        if not result:
            api_conversations = api.fetch_channels()
            db.save_conversations(api_conversations)
            result = db.fetch_channel(channel_name=conversation_name)
    else:
        result = db.fetch_chat(chat_name=conversation_name)
        if not result:
            api_conversations = api.fetch_chats()
            db.save_conversations(api_conversations)
            result = db.fetch_chat(chat_name=conversation_name)

    return result


@function_tool
def send_message(ctx: RunContextWrapper[AssistantContext], message: str, conversation_id: str = None):
    """Sends a message to Slack

    Args:
        message: The content of the message.
        conversation_id: Conversation ID that represents a channel (prefixed with #) or a chat (prefixed with @).
    """

    slack_token = ctx.context.slack.api_token
    channel = get_conversation(slack_token, conversation_id)
    api = SlackAPI(slack_token)

    api.send_message(channel.id, message)


slack_agent = Agent(
    name="Slack agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are an agent specialized in operating with Slack.
""",
    tools=[
        send_message,
    ]
)
