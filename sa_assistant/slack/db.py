from typing import List
from sqlmodel import select

from sa_assistant.db import get_session
from .models import SlackChannel, SlackChat


def fetch_channel(channel_name: str | None, channel_id: str | None) -> SlackChannel:
    db_session = get_session()

    with db_session as session:
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
