from agents import RunContextWrapper, Agent
from .context import AssistantContext


def my_team(ctx: RunContextWrapper[AssistantContext], agent: Agent[AssistantContext]):
    team = ",".join(ctx.context.team)
    return f"When asked about 'my team', I'm refering to {team}"
