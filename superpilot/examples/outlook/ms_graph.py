from dotenv import load_dotenv
import os
import requests
from gen_token import get_access_token  # Import the function from token.py

MS_GRAPH_BASE_URL = 'https://graph.microsoft.com/v1.0'

def send_email(access_token):
    url = f"{MS_GRAPH_BASE_URL}/me/sendMail"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    email_data = {
        "message": {
            "subject": "Test Email",
            "body": {
                "contentType": "Text",
                "content": "This is a test email sent from Python using Microsoft Graph API."
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": "recipient@example.com"
                    }
                }
            ]
        }
    }
    response = requests.post(url, json=email_data, headers=headers)
    if response.status_code == 202:
        print("Email sent successfully!")
    else:
        print(f"Failed to send email: {response.status_code}")
        print(response.json())

def read_emails(access_token):
    url = f"{MS_GRAPH_BASE_URL}/me/messages?$top=5"  # Fetch first 5 emails
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        emails = response.json().get('value', [])
        if emails:
            print("First 5 emails:")
            for i, email in enumerate(emails, 1):
                print(f"{i}. Subject: {email.get('subject', 'No Subject')}")
                print(f"   From: {email.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')}")
                print(f"   Received: {email.get('receivedDateTime', 'No Date')}")
                print("-" * 40)
        else:
            print("No emails found.")
    else:
        print(f"Failed to fetch emails: {response.status_code}")
        print(response.json())

def main():
    load_dotenv()  # Load environment variables from .env file
    APPLICATION_ID = os.getenv('APPLICATION_ID')  # Ensure these are correct
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')  # Ensure this is the actual secret, not the secret ID
    SCOPES = ['User.Read', 'Mail.ReadWrite', 'Mail.Send']
    
    try:
        access_token = get_access_token(APPLICATION_ID, CLIENT_SECRET, SCOPES)
        print("Access token acquired successfully.")
        print(access_token)
        
        # Send test email after acquiring the access token
        send_email(access_token)
        
        # Read first 5 emails
        read_emails(access_token)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
