import os
from dotenv import load_dotenv
import pyttsx3
import time
import requests
import csv
from daily_call import DailyCall
from twilio.rest import Client

# Load environment variables from .env file
load_dotenv()

class Vapi:
    def __init__(self, *, api_key, api_url="https://api.vapi.ai", twilio_sid=None, twilio_auth_token=None, twilio_phone_number=None, agent_id=None):
        self.api_key = api_key
        self.api_url = api_url
        self.__client = None
        self.speaker = pyttsx3.init()  # Initialize the TTS engine
        self.twilio_sid = twilio_sid or os.getenv('TWILIO_SID')
        self.twilio_auth_token = twilio_auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = twilio_phone_number or os.getenv('TWILIO_PHONE_NUMBER')
        self.twilio_client = None  # Initialize Twilio client as None
        self.call_id = None  # Store the call ID for later use
        self.agent_id = agent_id or os.getenv('AGENT_ID')  # Load AGENT_ID from .env if not provided
        print("Vapi initialized with API key:", self.api_key)

        # Initialize Twilio client if credentials are provided
        if self.twilio_sid and self.twilio_auth_token:
            self.twilio_client = Client(self.twilio_sid, self.twilio_auth_token)
            print("Twilio client initialized.")
        else:
            print("Twilio credentials not provided.")

    def start(self, *, assistant_id=None, assistant=None, assistant_overrides=None, squad_id=None, squad=None, outbound_numbers=None):
        print("Starting call...")
        if self.__client:
            print("Stopping active call before starting a new one.")
            self.stop()

        if assistant_id:
            payload = {'assistantId': assistant_id, 'assistantOverrides': assistant_overrides}
        elif assistant:
            payload = {'assistant': assistant, 'assistantOverrides': assistant_overrides}
        elif squad_id:
            payload = {'squadId': squad_id}
        elif squad:
            payload = {'squad': squad}
        else:
            raise Exception("Error: No assistant specified.")
        
        # Include agent_id in the payload
        payload['agentId'] = self.agent_id
        print(f"Making API call with payload: {payload}")

        try:
            # Capture the call_id here
            self.call_id, web_call_url = self.create_web_call(payload)
            print(f"Received call ID: {self.call_id}, Web call URL: {web_call_url}")

            if not web_call_url:
                raise Exception("Error: Unable to create call.")
            
            print(f"Joining call with ID {self.call_id}...")
            self.__client = DailyCall()
            self.__client.join(web_call_url)
            print("Successfully joined the call.")

            self.speak_text("Call successfully joined! I'm ready to assist.") 

            if outbound_numbers:
                for number in outbound_numbers:
                    self.make_outbound_call(number)

        except Exception as e:
            print(f"Error during call creation: {e}")
            
    def get_transcript(self):
        """
        Retrieves the transcript of the call by its call_id from the API.
        """
        if not self.call_id:
            print("Error: No call has been started yet.")
            return None

        try:
            url = f"{self.api_url}/call/{self.call_id}/transcript"
            headers = {
                'Authorization': 'Bearer ' + self.api_key
            }
            response = requests.get(url, headers=headers)
            print(f"API response status: {response.status_code}")

            if response.status_code == 200:
                transcript_data = response.json()
                transcript = transcript_data.get('transcript')
                if transcript:
                    return transcript
                else:
                    raise Exception("Error: No transcript available.")
            else:
                raise Exception(f"Error: {response.json().get('message', 'Unknown error occurred')}")
        except Exception as e:
            print(f"Failed to retrieve transcript: {e}")
            return None
        
    def save_transcript_to_txt(self, file_path):
        """
        Retrieves the transcript and saves it to a .txt file.
        """
        transcript = self.get_transcript()
        if transcript:
            try:
                with open(file_path, 'w') as file:
                    file.write(transcript)
                print(f"Transcript saved to {file_path}")
            except Exception as e:
                print(f"Failed to save transcript: {e}")
        else:
            print("No transcript to save.")
        
    def speak_text(self, text):
        """
        Convert the given text to speech and play it.
        """
        print(f"Speaking: {text}")
        self.speaker.say(text)
        self.speaker.runAndWait()  

    def stop(self):
        print("Stopping call...")
        if self.__client:
            try:
                self.__client.leave()  
                print("Left the call successfully.")
            except Exception as e:
                print(f"Error stopping call: {e}")
            finally:
                self.__client = None  
                print("Client reset.")
        else:
            print("No active call to stop.")

    def send(self, message):
        if not self.__client:
            raise Exception("Call not started. Please start the call first.")
        
        if not isinstance(message, dict) or 'type' not in message:
            raise ValueError("Invalid message format.")

        try:
            self.__client.send_app_message(message)
            print(f"Message sent: {message}")
        except Exception as e:
            print(f"Failed to send message: {e}")

    def add_message(self, role, content):
        message = {
            'type': 'add-message',
            'message': {
                'role': role,
                'content': content
            }
        }
        self.send(message)

    def create_web_call(self, payload):
        print(f"Making API request with payload: {payload}")
        url = f"{self.api_url}/call/web"
        headers = {
            'Authorization': 'Bearer ' + self.api_key,
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, json=payload)
        print(f"API response status: {response.status_code}")

        if response.status_code == 201:
            data = response.json()
            call_id = data.get('id')
            web_call_url = data.get('webCallUrl')
            if call_id and web_call_url:
                return call_id, web_call_url
            else:
                raise Exception("Error: Missing call ID or web call URL.")
        else:
            raise Exception(f"Error: {response.json().get('message', 'Unknown error occurred')}")

    def send_sms(self, to, body):
        """
        Sends an SMS to the specified phone number via Twilio.
        """
        if not self.twilio_client:
            raise Exception("Twilio client is not initialized.")
        try:
            message = self.twilio_client.messages.create(
                body=body,
                from_=self.twilio_phone_number,
                to=to
            )
            print(f"SMS sent: {message.sid}")
        except Exception as e:
            print(f"Failed to send SMS: {e}")

    def make_outbound_call(self, to):
        """
        Initiates an outbound call to the provided phone number via Twilio.
        """
        if not self.twilio_client:
            raise Exception("Twilio client is not initialized.")
        
        twilio_configuration_id = "443224f7-9d43-4f5c-9599-4ddb62831642"
        print(f"Using Twilio configuration ID: {twilio_configuration_id}")
        
        try:
            url = "http://demo.twilio.com/docs/voice.xml" 

            call = self.twilio_client.calls.create(
                to=to,  
                from_=self.twilio_phone_number,  
                url=url  
            )
            print(f"Outbound call initiated: {call.sid}")
        except Exception as e:
            print(f"Failed to initiate outbound call: {e}")


    def read_phone_numbers_from_csv(self, csv_file_path):
        """
        Reads a CSV file containing phone numbers and returns a list of phone numbers.
        """
        phone_numbers = []
        try:
            with open(csv_file_path, mode='r') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    phone_numbers.append(row[0])
            print(f"Phone numbers loaded: {phone_numbers}")
        except Exception as e:
            print(f"Failed to read CSV file: {e}")
        return phone_numbers

