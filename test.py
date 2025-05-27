from agents import Runner
from sa_assistant.context import AssistantContext
import sa_assistant
import asyncio
import yaml

config = yaml.load(open("config.yaml"), Loader=yaml.Loader)
context = AssistantContext(**config)


async def main():
    result = await Runner.run(
        sa_assistant.calendar_agent,
        "Tell me tomorrow's agenda",
        context=context,
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
