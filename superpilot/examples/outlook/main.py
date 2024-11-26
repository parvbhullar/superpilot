from flask import Flask, request
import msal
import requests
import webbrowser

# Azure AD app credentials (configured for delegated flow)
tenant_id = "tenant_id"
client_id = "client_id"
client_secret = "client_secret"
# Scopes for delegated permissions
scopes = ["User.Read", "Mail.Read", "Mail.Send", "Mail.ReadWrite"]
redirect_uri = "http://localhost:8880"

# Redirect URI for your app (configured in Azure AD app registration)
app = msal.ConfidentialClientApplication(
    client_id,
    client_credential=client_secret,
    authority=f"https://login.microsoftonline.com/{tenant_id}"
)

# Use the client credentials flow
result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

auth_url = app.get_authorization_request_url(scopes, redirect_uri=redirect_uri)
print(f"Please visit this URL to authorize the app: {auth_url}")
webbrowser.open(auth_url)

flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    code = request.args.get('code')
    if code:
        print(f"Authorization code received: {code}")
        result = app.acquire_token_by_authorization_code(code, scopes, redirect_uri=redirect_uri)

        if "access_token" in result:
            access_token = result["access_token"]
            print("Access token acquired:", access_token)

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            graph_api_url = "https://graph.microsoft.com/v1.0/me/messages"

            # Initialize variable to hold all email messages
            all_messages = []

            # Fetch all pages of messages
            while graph_api_url:
                response = requests.get(graph_api_url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    messages = data.get('value', [])
                    all_messages.extend(messages)  # Add the current page of messages

                    # Check if there's a next page and update the URL
                    graph_api_url = data.get('@odata.nextLink')
                    print(f"Fetched {len(messages)} messages, moving to next page...")
                else:
                    print(f"Error fetching emails: {response.status_code}, {response.text}")
                    break

            # Process the messages
            if all_messages:
                print(f"Total emails fetched: {len(all_messages)}")
                for i, message in enumerate(all_messages[:5], 1):  # Display first 5 emails
                    print(f"Email {i}:")
                    print(f"  Subject: {message.get('subject', 'No Subject')}")
                    print(f"  Sender: {message.get('from', {}).get('emailAddress', {}).get('address', 'Unknown Sender')}")
                    print(f"  Body Preview: {message.get('bodyPreview', 'No preview available')}")
                    print("-" * 50)
            else:
                print("No emails found.")
            
            return "Authorization complete! You can now close this window."
        else:
            return f"Error getting token: {result.get('error_description')}"
    else:
        return "No authorization code found."

flask_app.run(port=8880)
