import os
import json
from pathlib import Path

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive',
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

    def get_calendar_service(self):
        return build('calendar', 'v3', credentials=self.get_credentials())

    def get_drive_service(self):
        return build('drive', 'v3', credentials=self.get_credentials())
