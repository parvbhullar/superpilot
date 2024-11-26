import os
import base64 
import traceback
import BeautifulSoup
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']  

class GoogleService:
    """Class to handle Gmail API authentication and email processing."""

    def __init__(self, creds_file):
        self.creds_file = creds_file
        self.service = self.authenticate_gmail()

    def authenticate_gmail(self):
        """Authenticate with the Gmail API using OAuth2."""
        creds = None

        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Token refresh failed: {e}")
                    creds = None
            if not creds:
                flow = InstalledAppFlow.from_client_secrets_file(self.creds_file, SCOPES)
                creds = flow.run_local_server(port=0)

            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        service = build('gmail', 'v1', credentials=creds)
        return service

    def decode_body(self, body_data, is_html=False):
        """Decode the email body from base64 encoding."""
        body_decoded = base64.urlsafe_b64decode(body_data.encode('ASCII')).decode('utf-8')

        if is_html:
            soup = BeautifulSoup(body_decoded, 'html.parser')
            body_decoded = soup.get_text()

        return body_decoded

    def list_messages(self, user_id='me'):
        """List the emails from the Gmail account."""
        try:
            results = self.service.users().messages().list(userId=user_id).execute()
            messages = results.get('messages', [])

            if not messages:
                print('No messages found.')
            else:
                print('Messages:')
                for message in messages[:5]:
                    msg = self.service.users().messages().get(userId=user_id, id=message['id']).execute()
                    snippet = msg['snippet']

                    payload = msg['payload']
                    headers = payload['headers']

                    subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')
                    sender = next((header['value'] for header in headers if header['name'] == 'From'), 'No Sender')

                    body = ''

                    if 'parts' in payload:
                        for part in payload['parts']:
                            if part['mimeType'] == 'text/plain':
                                body = self.decode_body(part['body']['data'], is_html=False)
                                break
                            elif part['mimeType'] == 'text/html':
                                body = self.decode_body(part['body']['data'], is_html=True)
                    else:
                        if payload.get('body', {}).get('data'):
                            body = self.decode_body(payload['body']['data'], is_html=False)

                    print(f"Subject: {subject}")
                    print(f"From: {sender}")
                    print(f"Snippet: {snippet}")
                    print(f"Body: {body[:200]}...")
                    print('-' * 50)

        except Exception as error:
            print(f'An error occurred: {error}')
            traceback.print_exc()

