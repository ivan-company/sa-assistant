import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from io import BytesIO

from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload, MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from .models import CalendarEvent


SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents.readonly',
]


class GoogleAPI:
    def __init__(self):
        self.client_secrets_file = Path("google_secrets.json")
        self.credentials_file = Path("google_credentials.json")

    def authenticate_once(self):
        flow = InstalledAppFlow.from_client_secrets_file(
            self.client_secrets_file, SCOPES)
        credentials = flow.run_local_server(port=0)

        self.save_credentials(credentials)

    def save_credentials(self, credentials):
        creds_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

        with open(self.credentials_file, 'w') as f:
            json.dump(creds_data, f)
        os.chmod(self.credentials_file, 0o600)

    def load_credentials(self):
        if not self.credentials_file.exists():
            return None

        with open(self.credentials_file, 'r') as f:
            creds_data = json.load(f)

        return Credentials(**creds_data)

    def get_credentials(self):
        credentials = self.load_credentials()

        if not credentials:
            credentials = self.authenticate_once()

        if credentials.expired:
            credentials.refresh()
            self.save_credentials(credentials)

        return credentials

    def get_service(self):
        raise NotImplementedError


class GoogleCalendarAPI(GoogleAPI):
    def get_service(self):
        return build('calendar', 'v3', credentials=self.get_credentials())

    def delete_event(self, event_id: str, calendar_id='primary') -> CalendarEvent:
        service = self.get_service()
        event = service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()

        event_summary = event.get('summary', 'No title')
        event_start = event['start'].get(
            'dateTime', event['start'].get('date'))

        # Delete the event
        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()

        return CalendarEvent(
            id=event_id,
            summary=event_summary,
            start=event_start,
        )

    def get_events(self, calendar_id: str, time_min: str, time_max: str, max_results: int, order_by: str) -> List[CalendarEvent]:
        print("getting events")
        events_result = self.get_service().events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy=order_by
        ).execute()

        events = events_result.get('items', [])

        # Format events for better readability
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            formatted_event = CalendarEvent(
                id=event.get('id'),
                summary=event.get('summary', 'No title'),
                start=start,
                end=end,
                description=event.get('description', ''),
                location=event.get('location', ''),
                attendees=[attendee.get('email')
                           for attendee in event.get('attendees', [])]
            )
            formatted_events.append(formatted_event)

        return formatted_events

    def create_event(self, calendar_id, event_body) -> CalendarEvent:
        created_event = self.get_service().events().insert(
            calendarId=calendar_id,
            body=event_body
        ).execute()

        return CalendarEvent(
            id=created_event.get('id'),
            summary=created_event.get('summary'),
            start=created_event['start'].get('dateTime'),
            end=created_event['end'].get('dateTime'),
            html_link=created_event.get('htmlLink'),
        )


class GoogleDriveAPI(GoogleAPI):
    """Google Drive API wrapper for file and folder operations."""

    def get_service(self) -> Resource:
        return build('drive', 'v3', credentials=self.get_credentials())

    def read_file(self, file_id: str, download_path: Optional[str] = None) -> Union[bytes, str]:
        """
        Read/download a file from Google Drive.

        Args:
            file_id: The ID of the file to read
            download_path: Optional path to save the file locally. If not provided, returns file content

        Returns:
            File content as bytes if download_path is None, otherwise returns download_path
        """
        try:
            service = self.get_service()

            # Get file metadata first
            file_metadata = service.files().get(fileId=file_id).execute()

            # Check if it's a Google Workspace file (Docs, Sheets, etc.)
            mime_type = file_metadata.get('mimeType', '')

            if mime_type.startswith('application/vnd.google-apps'):
                # Handle Google Workspace files differently
                return self._export_google_file(file_id, mime_type, download_path)

            # Regular file download
            request = service.files().get_media(fileId=file_id)

            if download_path:
                # Download to file
                with open(download_path, 'wb') as f:
                    downloader = MediaIoBaseDownload(f, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                        if status:
                            print(f"Download progress: {
                                  int(status.progress() * 100)}%")
                return download_path
            else:
                # Download to memory
                file_content = BytesIO()
                downloader = MediaIoBaseDownload(file_content, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()

                return file_content.getvalue()

        except HttpError as error:
            print(f"An error occurred: {error}")
            raise

    def _export_google_file(self, file_id: str, mime_type: str, download_path: Optional[str] = None) -> Union[bytes, str]:
        """Export Google Workspace files to compatible formats."""
        service = self.get_service()

        # Define export MIME types for Google Workspace files
        export_mappings = {
            'application/vnd.google-apps.document': 'application/pdf',
            'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.google-apps.presentation': 'application/pdf',
            'application/vnd.google-apps.drawing': 'image/png',
        }

        export_mime_type = export_mappings.get(mime_type, 'application/pdf')

        request = service.files().export_media(
            fileId=file_id,
            mimeType=export_mime_type
        )

        if download_path:
            with open(download_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            return download_path
        else:
            file_content = BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            return file_content.getvalue()

    def create_file(self,
                    name: str,
                    content: Optional[Union[str, bytes]] = None,
                    file_path: Optional[str] = None,
                    mime_type: Optional[str] = None,
                    parent_folder_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new file in Google Drive.

        Args:
            name: Name of the file
            content: File content as string or bytes (use this or file_path)
            file_path: Path to local file to upload (use this or content)
            mime_type: MIME type of the file. If not provided, will be auto-detected
            parent_folder_id: ID of the parent folder. If not provided, creates in root

        Returns:
            Dictionary containing file metadata including ID
        """
        try:
            service = self.get_service()

            file_metadata = {'name': name}

            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]

            if file_path:
                # Upload from file
                if not mime_type:
                    # Auto-detect MIME type
                    import mimetypes
                    mime_type = mimetypes.guess_type(
                        file_path)[0] or 'application/octet-stream'

                media = MediaFileUpload(
                    file_path, mimetype=mime_type, resumable=True)
            elif content is not None:
                # Upload from memory
                if isinstance(content, str):
                    content = content.encode('utf-8')
                    if not mime_type:
                        mime_type = 'text/plain'

                if not mime_type:
                    mime_type = 'application/octet-stream'

                media = MediaIoBaseUpload(
                    BytesIO(content), mimetype=mime_type, resumable=True)
            else:
                # Create empty file
                media = None

            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, mimeType, parents, webViewLink, createdTime'
            ).execute()

            print(f"File created: {file.get('name')} (ID: {file.get('id')})")
            return file

        except HttpError as error:
            print(f"An error occurred: {error}")
            raise

    def update_file(self,
                    file_id: str,
                    name: Optional[str] = None,
                    content: Optional[Union[str, bytes]] = None,
                    file_path: Optional[str] = None,
                    mime_type: Optional[str] = None,
                    add_parents: Optional[List[str]] = None,
                    remove_parents: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Update an existing file in Google Drive.

        Args:
            file_id: ID of the file to update
            name: New name for the file (optional)
            content: New file content as string or bytes (optional)
            file_path: Path to local file with new content (optional)
            mime_type: MIME type of the new content
            add_parents: List of parent folder IDs to add
            remove_parents: List of parent folder IDs to remove

        Returns:
            Dictionary containing updated file metadata
        """
        try:
            service = self.get_service()

            file_metadata = {}
            if name:
                file_metadata['name'] = name

            media = None
            if file_path:
                if not mime_type:
                    import mimetypes
                    mime_type = mimetypes.guess_type(
                        file_path)[0] or 'application/octet-stream'
                media = MediaFileUpload(
                    file_path, mimetype=mime_type, resumable=True)
            elif content is not None:
                if isinstance(content, str):
                    content = content.encode('utf-8')
                    if not mime_type:
                        mime_type = 'text/plain'
                if not mime_type:
                    mime_type = 'application/octet-stream'
                media = MediaIoBaseUpload(
                    BytesIO(content), mimetype=mime_type, resumable=True)

            # Build update parameters
            update_params = {
                'fileId': file_id,
                'fields': 'id, name, mimeType, parents, webViewLink, modifiedTime'
            }

            if file_metadata:
                update_params['body'] = file_metadata

            if media:
                update_params['media_body'] = media

            if add_parents:
                update_params['addParents'] = ','.join(add_parents)

            if remove_parents:
                update_params['removeParents'] = ','.join(remove_parents)

            file = service.files().update(**update_params).execute()

            print(f"File updated: {file.get('name')} (ID: {file.get('id')})")
            return file

        except HttpError as error:
            print(f"An error occurred: {error}")
            raise

    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from Google Drive.

        Args:
            file_id: ID of the file to delete

        Returns:
            True if deletion was successful
        """
        try:
            service = self.get_service()
            service.files().delete(fileId=file_id).execute()
            print(f"File deleted: {file_id}")
            return True
        except HttpError as error:
            print(f"An error occurred: {error}")
            raise

    def create_folder(self,
                      name: str,
                      parent_folder_id: Optional[str] = None,
                      description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new folder in Google Drive.

        Args:
            name: Name of the folder
            parent_folder_id: ID of the parent folder. If not provided, creates in root
            description: Optional description for the folder

        Returns:
            Dictionary containing folder metadata including ID
        """
        try:
            service = self.get_service()

            file_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]

            if description:
                file_metadata['description'] = description

            folder = service.files().create(
                body=file_metadata,
                fields='id, name, mimeType, parents, webViewLink, createdTime'
            ).execute()

            print(f"Folder created: {folder.get(
                'name')} (ID: {folder.get('id')})")
            return folder

        except HttpError as error:
            print(f"An error occurred: {error}")
            raise

    # Additional utility methods

    def list_files(self,
                   query: Optional[str] = None,
                   page_size: int = 100,
                   fields: str = "files(id, name, mimeType, parents, createdTime, modifiedTime, size, shortcutDetails)") -> List[Dict[str, Any]]:
        """
        List files in Google Drive based on query.

        Args:
            query: Search query (e.g., "'folder_id' in parents", "name contains 'test'")
            page_size: Number of files per page
            fields: Fields to include in response

        Returns:
            List of file metadata dictionaries
        """
        try:
            service = self.get_service()
            results = []
            page_token = None

            while True:
                response = service.files().list(
                    q=query,
                    pageSize=page_size,
                    fields=f"nextPageToken, {fields}",
                    pageToken=page_token
                ).execute()

                results.extend(response.get('files', []))
                page_token = response.get('nextPageToken')

                if not page_token:
                    break

            return results

        except HttpError as error:
            print(f"An error occurred: {error}")
            raise

    def get_folder_id_by_path(self, folder_path: str, create_if_not_exists: bool = False, search_shared: bool = True) -> Optional[str]:
        """
        Get folder ID from a path like 'a/b/c'.

        Args:
            folder_path: Path to the folder (e.g., 'a/b/c' or '/a/b/c')
            create_if_not_exists: If True, creates missing folders in the path
            search_shared: If True, also searches in shared folders for the first folder in path

        Returns:
            Folder ID if found/created, None otherwise
        """
        print(f"Getting folder ID by path: {folder_path}")
        # Clean the path
        folder_path = folder_path.strip('/')
        if not folder_path:
            return 'root'

        folders = folder_path.split('/')
        parent_id = 'root'

        for i, folder_name in enumerate(folders):
            print(f"Processing folder: {folder_name}")
            # Build the query - include both folder and shortcut MIME types
            mime_query = "(mimeType = 'application/vnd.google-apps.folder' or mimeType = 'application/vnd.google-apps.shortcut')"

            if i == 0 and search_shared:
                # For the first folder, search both in My Drive and shared folders
                query = f"name = '{folder_name}' and {
                    mime_query} and trashed = false"
                if parent_id == 'root':
                    # Include both root and shared folders
                    query = f"('{parent_id}' in parents or sharedWithMe = true) and {
                        query}"
                else:
                    query = f"'{parent_id}' in parents and {query}"
            else:
                # For subsequent folders, only search within the parent
                query = f"'{parent_id}' in parents and name = '{
                    folder_name}' and {mime_query} and trashed = false"

            results = self.list_files(query=query)

            if results:
                # Found - could be folder or shortcut
                found_item = results[0]

                # If it's a shortcut, get the target ID
                if found_item.get('mimeType') == 'application/vnd.google-apps.shortcut':
                    shortcut_details = found_item.get('shortcutDetails', {})
                    target_id = shortcut_details.get('targetId')
                    if target_id:
                        parent_id = target_id
                    else:
                        # Couldn't resolve shortcut
                        return None
                else:
                    # Regular folder
                    parent_id = found_item['id']
            elif create_if_not_exists:
                # Create the folder only if we have write permission
                try:
                    new_folder = self.create_folder(
                        name=folder_name, parent_folder_id=parent_id)
                    parent_id = new_folder['id']
                except HttpError as error:
                    if error.resp.status == 403:
                        print(f"No permission to create folder '{
                              folder_name}' in parent")
                        return None
                    raise
            else:
                print(f"Folder not found: {folder_name}")
                # Folder not found and not creating
                return None

        return parent_id

    def find_file_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Find a file by its full path.

        Args:
            file_path: Full path to the file (e.g., 'a/b/c/test.txt')

        Returns:
            File metadata if found, None otherwise
        """
        # Split path and filename
        path_parts = file_path.strip('/').split('/')
        if len(path_parts) == 1:
            # File is in root
            folder_id = 'root'
            file_name = path_parts[0]
        else:
            # File is in a subfolder
            folder_path = '/'.join(path_parts[:-1])
            file_name = path_parts[-1]
            folder_id = self.get_folder_id_by_path(folder_path)

            if not folder_id:
                return None

        # Search for the file in the folder
        query = f"'{folder_id}' in parents and name = '{
            file_name}' and trashed = false"
        files = self.list_files(query=query)

        if files:
            return files[0]
        return None

    def create_file_by_path(self,
                            file_path: str,
                            content: Optional[Union[str, bytes]] = None,
                            local_file_path: Optional[str] = None,
                            mime_type: Optional[str] = None,
                            create_folders: bool = True) -> Dict[str, Any]:
        """
        Create a file at a specific path, optionally creating folders.

        Args:
            file_path: Full path where to create the file (e.g., 'a/b/c/test.txt')
            content: File content as string or bytes
            local_file_path: Path to local file to upload
            mime_type: MIME type of the file
            create_folders: If True, creates missing folders in the path

        Returns:
            File metadata
        """
        # Split path and filename
        path_parts = file_path.strip('/').split('/')
        if len(path_parts) == 1:
            # File is in root
            folder_id = None
            file_name = path_parts[0]
        else:
            # File is in a subfolder
            folder_path = '/'.join(path_parts[:-1])
            file_name = path_parts[-1]
            folder_id = self.get_folder_id_by_path(
                folder_path, create_if_not_exists=create_folders)

            if not folder_id and not create_folders:
                raise ValueError(f"Folder path '{folder_path}' does not exist")

        return self.create_file(
            name=file_name,
            content=content,
            file_path=local_file_path,
            mime_type=mime_type,
            parent_folder_id=folder_id
        )

    def list_files_in_path(self, folder_path: str, recursive: bool = False) -> List[Dict[str, Any]]:
        """
        List all files in a folder specified by path.

        Args:
            folder_path: Path to the folder (e.g., 'a/b/c')
            recursive: If True, includes files from subfolders

        Returns:
            List of file metadata
        """
        folder_id = self.get_folder_id_by_path(folder_path)
        if not folder_id:
            return []

        if not recursive:
            return self.list_files(query=f"'{folder_id}' in parents and trashed = false")

        # For recursive listing, we need to get all descendants
        all_files = []
        folders_to_process = [folder_id]
        processed_folders = set()

        while folders_to_process:
            current_folder = folders_to_process.pop(0)
            print(f"processing {current_folder}")
            print(folders_to_process)
            if current_folder in processed_folders:
                continue
            processed_folders.add(current_folder)

            # Get all items in current folder
            items = self.list_files(
                query=f"'{current_folder}' in parents and trashed = false")

            for item in items:
                all_files.append(item)
                # If it's a folder, add it to process list
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    folders_to_process.append(item['id'])

        return all_files

    def download_file_by_path(self, file_path: str, local_download_path: Optional[str] = None) -> Union[bytes, str]:
        """
        Download a file specified by its path.

        Args:
            file_path: Full path to the file (e.g., 'a/b/c/test.txt')
            local_download_path: Local path where to save the file

        Returns:
            File content as bytes or local path if downloaded to disk
        """
        file = self.find_file_by_path(file_path)
        if not file:
            raise FileNotFoundError(f"File not found: {file_path}")

        return self.read_file(file['id'], download_path=local_download_path)


class GoogleDocsAPI(GoogleAPI):
    def get_service(self):
        return build('docs', 'v1', credentials=self.get_credentials())

    def get_document(self, document_id: str) -> dict:
        service = self.get_service()
        return service.documents().get(documentId=document_id).execute()

    def extract_data(self, document_id: str) -> str:
        doc_json = self.get_document(document_id)
        text_chunks = []
        for element in doc_json.get('body', {}).get('content', []):
            if 'table' in element:
                text_chunks.append(self._extract_table(element))
            elif 'paragraph' in element:
                paragraph = self._extract_paragraph(element)
                if paragraph:
                    text_chunks.append(paragraph)
        return text_chunks

    def _extract_paragraph(self, element) -> str:
        result = []
        # Detect heading style
        para_style = element['paragraph'].get('paragraphStyle', {})
        named_style = para_style.get('namedStyleType', '')
        heading_level = None
        if named_style.startswith('HEADING_'):
            try:
                heading_level = int(named_style.split('_')[1])
            except Exception:
                heading_level = None
        for e in element['paragraph'].get('elements', []):
            if 'textRun' in e:
                content = e['textRun'].get('content', '')
                if content.endswith("\n"):
                    content = content[:-1]
                if content.strip() not in ["", "\n"]:
                    if heading_level:
                        result.append(
                            f"{'#' * heading_level} {content.strip()}")
                    else:
                        result.append(content)
        return ''.join(result).strip()

    def _clean_cells(self, cells):
        cleaned_cells = []
        for cell in cells:
            text_cell = self._extract_cell_text_simple(cell)
            if text_cell.strip() not in ["", "\n"]:
                cleaned_cells.append(cell)
        return cleaned_cells

    def _is_colored(self, cell):
        # Returns True if the cell's background is not white (or missing)
        style = cell.get('tableCellStyle', {})
        color = style.get('backgroundColor', {}).get(
            'color', {}).get('rgbColor', {})
        # Default to white if not specified
        r = color.get('red', 1)
        g = color.get('green', 1)
        b = color.get('blue', 1)
        # Consider as colored if any channel is not 1 (not white)
        return (r, g, b) != (1, 1, 1)

    def _extract_cell_text_simple(self, cell):
        # Simple text extraction for table cell (no chips)
        text = ''
        for p in cell.get('content', []):
            for e in p.get('paragraph', {}).get('elements', []):
                if 'textRun' in e:
                    text += e['textRun'].get('content', '')
        return text.strip()

    def _extract_table(self, element):
        table = element['table']
        rows = table['tableRows']
        if not rows:
            return ''
        n_cols = len(rows[0]['tableCells']) if rows[0]['tableCells'] else 0
        if n_cols == 0:
            return ''
        # Horizontal table: scan for multi-column colored header row, treat single-cell colored rows as titles
        formatted_output = []
        row_idx = 0
        while row_idx < len(rows):
            row = rows[row_idx]
            cells = row['tableCells']
            cells = self._clean_cells(cells)
            # If all cells are colored and only one cell, treat as title
            if len(cells) == 1 and self._is_colored(cells[0]):
                title = self._extract_cell_text_simple(cells[0])
                if title:
                    formatted_output.append(f"## {title}")
                row_idx += 1
                continue
            # If all cells are colored and more than one cell, treat as header row
            if len(cells) > 1 and all(self._is_colored(cell) for cell in cells):
                headers = [self._extract_cell_text_simple(
                    cell) for cell in cells]
                data_rows = rows[row_idx+1:]
                formatted_rows = []
                for i, data_row in enumerate(data_rows):
                    values = [self._extract_cell_text_simple(
                        cell) for cell in data_row['tableCells']]
                    if all(v == '' for v in values):
                        continue
                    formatted = f"{len(formatted_rows)+1}.\n"
                    for h, v in zip(headers, values):
                        formatted += f"  - {h if h else ''} -> {v}\n"
                    formatted_rows.append(formatted.rstrip())
                if formatted_rows:
                    formatted_output.append('\n'.join(formatted_rows))
                break  # Done with this table
            # Otherwise, not a header row, move to next row
            row_idx += 1
        # If not horizontal, check for vertical header (all first column cells colored)
        else:
            if all(self._is_colored(row['tableCells'][0]) for row in rows):
                headers = [self._extract_cell_text_simple(
                    row['tableCells'][0]) for row in rows]
                formatted_cols = []
                n_cols = len(rows[0]['tableCells'])
                for col_idx in range(1, n_cols):
                    values = [self._extract_cell_text_simple(
                        row['tableCells'][col_idx]) for row in rows]
                    if all(v == '' for v in values):
                        continue
                    formatted = f"{len(formatted_cols)+1}.\n"
                    for h, v in zip(headers, values):
                        formatted += f"  - {h if h else ''} -> {v}\n"
                    formatted_cols.append(formatted.rstrip())
                if formatted_cols:
                    formatted_output.append('\n'.join(formatted_cols))
        return '\n'.join(formatted_output) if formatted_output else ''
