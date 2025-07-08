import os 
from agents import Runner, RunConfig
from sa_assistant.context import AssistantContext
from sa_assistant.google.api import GoogleDriveAPI
import sa_assistant
import asyncio
import yaml

config = yaml.load(open("config.yaml"), Loader=yaml.Loader)
context = AssistantContext(**config)


async def main():
    # Create RunConfig with the model from context - currently only used for model selection
    run_config = RunConfig(model=context.openai_model)

    os.environ["OPENAI_API_KEY"] = config["openai_api_key"]

    result = await Runner.run(
        sa_assistant.jira_agent,
        "Help me summarize sprint goal for the 'GROW' project, in the current sprint.",
        context=context,
        run_config=run_config,
    )
    print(result.final_output)


async def test_google_drive():
    drive_api = GoogleDriveAPI()

    # file = drive_api.create_file(
    #     name="test file.txt",
    #     content="Hello, World!",
    #     mime_type="text/plain"
    # )
    #
    # folder = drive_api.create_folder("test folder")

    # all_files = drive_api.list_files_in_path(
    #     "Product Management/Creatives/PRDs/Documentation in Progress", recursive=True)

    # print(all_files)
    # drive_api.debug_find_item("Product Management")


async def test_slack_agent():
    """Test the slack agent by sending a test message"""
    run_config = RunConfig(model=context.openai_model)
    
    # Test sending a message to a channel (replace with your actual channel)
    result = await Runner.run(
        sa_assistant.slack_agent,
        "Send a test message 'Hello from the AI assistant!' to @Winston Zhu",
        context=context,
        run_config=run_config,
    )
    print("Slack test result:", result.final_output)


async def test_slack_agent_dm():
    """Test the slack agent by sending a DM"""
    run_config = RunConfig(model=context.openai_model)
    
    # Test sending a DM (replace with actual username)
    result = await Runner.run(
        sa_assistant.slack_agent,
        "Send a direct message 'Hi! This is a test from the AI assistant.' to @winston.zhu",
        context=context,
        run_config=run_config,
    )
    print("Slack DM test result:", result.final_output)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "slack":
            asyncio.run(test_slack_agent())
        elif test_name == "slack-dm":
            asyncio.run(test_slack_agent_dm())
        elif test_name == "jira":
            asyncio.run(main())
        else:
            print("Available tests: slack, slack-dm, jira")
    else:
        # Default test
        asyncio.run(main())
