from agents import function_tool, RunContextWrapper
from sa_assistant.integrations.google.drive import GoogleDriveAPI

from ...context import AssistantContext


@function_tool
async def create_drive_file(
    ctx: RunContextWrapper[AssistantContext],
    file_name: str,
    file_content: str
):
    """Create a new file in the drive.

    Args:
        file_name: The name of the file
        file_content: The content of the file
    """
    return GoogleDriveAPI().create_file(file_name, file_content)


@function_tool
async def delete_drive_file(
    ctx: RunContextWrapper[AssistantContext],
    file_id: str
):
    """Delete a file from the drive.

    Args:
        file_id: The ID of the file to delete
    """
    return GoogleDriveAPI().delete_file(file_id)


@function_tool
async def list_files_in_path(
    ctx: RunContextWrapper[AssistantContext],
    path: str
):
    """List files in the drive.

    Args:
        path: The path to the folder to list files in
    """
    return GoogleDriveAPI().list_files_in_path(path)


@function_tool
async def read_drive_file_by_path(
    ctx: RunContextWrapper[AssistantContext],
    file_path: str
):
    """Read a file from the drive.

    Args:
        file_path: The path to the file to read
    """
    try:
        return GoogleDriveAPI().download_file_by_path(file_path)
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'file_path': file_path
        }
