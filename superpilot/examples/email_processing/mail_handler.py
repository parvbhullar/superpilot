import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "superpilot", "examples", "email_processing")))
from mail import Email  


def main():
    
    creds_file = 'path_to_your_credentials.json'

    try:
        email_processor = Email(creds_file)

        print("Fetching email list...")
        email_processor.list_messages()

        message_id = 'your_message_id' 
        to = 'recipient@example.com'    
        body_text = 'This is an automated response to your email.'  

        print("Sending reply...")
        email_processor.send_reply(message_id, to, body_text)
        print("Reply sent successfully.")

    except FileNotFoundError as e:
        print(f"Error: The credentials file '{creds_file}' was not found. Please check the path.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
