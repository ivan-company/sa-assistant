from sa_assistant.agents.triage import triage_agent
from sa_assistant.models import AssistantContext
from agents import Runner
import asyncio
import yaml

config = yaml.load(open("config.yaml"), Loader=yaml.Loader)
context = AssistantContext(**config)


async def main():
    result = await Runner.run(
        triage_agent,
        "Tell me all the in-progress tickets of Ivan Company",
        context=context,
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
