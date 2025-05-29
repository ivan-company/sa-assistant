from agents import Runner
from sa_assistant.context import AssistantContext
from sa_assistant.google.api import GoogleDriveAPI
import sa_assistant
import asyncio
import yaml

config = yaml.load(open("config.yaml"), Loader=yaml.Loader)
context = AssistantContext(**config)


async def main():
    result = await Runner.run(
        sa_assistant.drive_agent,
        "Make a summary of the file 'Product Management/Creatives/PRDs/Documentation in Progress/PRD: Generative AI and Creatives 2'",
        context=context,
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

if __name__ == "__main__":
    asyncio.run(main())
