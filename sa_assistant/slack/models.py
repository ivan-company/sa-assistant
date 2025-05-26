from sqlmodel import SQLModel, Field


class SlackConversation(SQLModel):
    id: str = Field(primary_key=True)
    name: str


class SlackChannel(SlackConversation, table=True):
    is_private: bool


class SlackChat(SlackConversation, table=True):
    real_name: str
