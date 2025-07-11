from agents import Agent
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from sa_assistant.tools.slack import send_message

slack_agent = Agent(
    name="Slack agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are an agent specialized in operating with Slack.
""",
    tools=[
        send_message,
    ],
)
