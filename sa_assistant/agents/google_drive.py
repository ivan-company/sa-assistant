from datetime import datetime

from agents import Agent, RunContextWrapper
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from sa_assistant.tools.google.drive import (
    create_drive_file,
    delete_drive_file,
    list_files_in_path,
    read_drive_file_by_path,
)
from ..context import AssistantContext


def drive_agent_instructions(ctx: RunContextWrapper[AssistantContext], agent: Agent[AssistantContext]):
    timezone = ctx.context.calendar.timezone
    return f"""{RECOMMENDED_PROMPT_PREFIX}
You are a Google Drive agent. Your job is to handle all tasks related to Google Drive, including:
- Creating, reading, updating, and deleting files and folders
- Listing files and folders in any directory
- Moving and renaming files or folders
- Sharing files or folders with others
- Searching for files or folders by name

Some relevant information:
- Today's date is {datetime.now().strftime("%Y-%m-%d")}.
- My timezone is {timezone}

**Guidelines:**
- Always confirm file/folder names and paths with the user if there is ambiguity.
- If you encounter an error or cannot find a file/folder, inform the user and suggest next steps.
- If you are unsure about a request, ask the user for clarification.

**Examples:**
- "Create a file named 'report.txt' in the 'Projects' folder."
- "List all files in the 'Invoices/2024' folder."
- "Share 'presentation.pdf' with alice@example.com."
"""


drive_agent = Agent(
    name="Drive agent",
    instructions=drive_agent_instructions,
    tools=[
        create_drive_file,
        delete_drive_file,
        list_files_in_path,
        read_drive_file_by_path,
    ]
)
