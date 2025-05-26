from agents import Runner
from sa_assistant.context import AssistantContext
from sa_assistant.daily_check.agent import daily_checks_agent
import asyncio
import yaml

config = yaml.load(open("config.yaml"), Loader=yaml.Loader)
context = AssistantContext(**config)


async def main():
    result = await Runner.run(
        daily_checks_agent,
        "Perform my daily checks",
        context=context,
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
