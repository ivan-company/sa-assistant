from typing import List
from sqlmodel import select
from agents import RunContextWrapper, function_tool

from sa_assistant.context import AssistantContext
from sa_assistant.db import get_session
from sa_assistant.integrations.slack import SlackAPI, SlackChannel, SlackChat, SlackConversation


def fetch_channel(channel_id: str | None = None, channel_name: str | None = None) -> SlackChannel:
    db_session = get_session()

    with db_session as session:
        statement = None
        if channel_id:
            statement = select(SlackChannel).where(
                SlackChannel.id == channel_id)
        elif channel_name:
            statement = select(SlackChannel).where(
                SlackChannel.name == channel_name)
        results = session.exec(statement)

        return results.first()


def fetch_chat(chat_name: str) -> SlackChat:
    db_session = get_session()

    with db_session as session:
        statement = select(SlackChat).where(SlackChat.name == chat_name)
        results = session.exec(statement)

        return results.first()


def fetch_conversation(conversation_id: str) -> SlackChannel | SlackChat:
    if (conversation_id.startswith("#")):
        return fetch_channel(conversation_id[1:])

    return fetch_chat(conversation_id)


def save_conversations(conversations: List[SlackChannel | SlackChat]):
    db_session = get_session()

    with db_session as session:
        for conversation in conversations:
            session.add(conversation)

        session.commit()


def get_conversation(slack_token: str, conversation_id: str) -> SlackConversation:
    api = SlackAPI(slack_token)
    result = None
    conversation_name = conversation_id[1:]
    if conversation_id.startswith("#"):
        result = fetch_channel(channel_name=conversation_name)
        if not result:
            api_conversations = api.fetch_channels()
            save_conversations(api_conversations)
            result = fetch_channel(channel_name=conversation_name)
    else:
        result = fetch_chat(chat_name=conversation_name)
        if not result:
            api_conversations = api.fetch_chats()
            save_conversations(api_conversations)
            result = fetch_chat(chat_name=conversation_name)

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
