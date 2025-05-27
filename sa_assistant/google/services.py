class CalendarService:
    def __init__(self, client_secrets_file, scopes):
        self.client_secrets_file = client_secrets_file
        self.credentials_file = Path("calendar_credentials.json")
        self.scopes = scopes

    def authenticate_once(self):
        flow = InstalledAppFlow.from_client_secrets_file(
            self.client_secrets_file, self.scopes)
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
        credentials = self.get_credentials()
        service = build('calendar', 'v3', credentials=credentials)

        return service
