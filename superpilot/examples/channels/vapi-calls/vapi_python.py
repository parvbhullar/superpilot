import pyttsx3
import time
import requests
import csv
import json
import speech_recognition as sr
from daily_call import DailyCall
from twilio.rest import Client

class Vapi:
    def __init__(self, *, api_key, api_url="https://api.vapi.ai", twilio_sid=None, twilio_auth_token=None, twilio_phone_number=None, openai_api_key=None):
        self.api_key = api_key
        self.api_url = api_url
        self.twilio_sid = twilio_sid
        self.twilio_auth_token = twilio_auth_token
        self.twilio_phone_number = twilio_phone_number
        self.openai_api_key = openai_api_key
        self.speaker = pyttsx3.init()
        self._client = None
        self.conversation_log = []
        print("Vapi initialized with API key:", self.api_key)

        if self.twilio_sid and self.twilio_auth_token:
            self.twilio_client = Client(self.twilio_sid, self.twilio_auth_token)

        # Set up OpenAI API key
        if self.openai_api_key:
            openai.api_key = self.openai_api_key

    def start(self, *, assistant_id=None, assistant=None, assistant_overrides=None, squad_id=None, squad=None, outbound_numbers=None):
        print("Starting call...")
        if self._client:  # Corrected from __client to _client
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
        
        print(f"Making API call with payload: {payload}")

        try:
            call_id, web_call_url = self.create_web_call(payload)
            print(f"Received call ID: {call_id}, Web call URL: {web_call_url}")

            if not web_call_url:
                raise Exception("Error: Unable to create call.")
            
            print(f"Joining call with ID {call_id}...")
            self._client = DailyCall()  # Corrected from __client to _client
            self._client.join(web_call_url)
            print("Successfully joined the call.")

            self.speak_text("Call successfully joined! I'm ready to assist.") 

            if outbound_numbers:
                for number in outbound_numbers:
                    self.make_outbound_call(number)

            # Start listening for the conversation
            self.listen_for_conversation()

        except Exception as e:
            print(f"Error during call creation: {e}")



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

    def listen_for_conversation(self):
        """
        Listen to the conversation, recognize speech, and respond dynamically.
        """
        recognizer = sr.Recognizer()

        with sr.Microphone() as source:
            print("Listening for speech... (Say 'stop' to end)")
            while True:
                try:
                    recognizer.adjust_for_ambient_noise(source)
                    audio = recognizer.listen(source, timeout=5)
                    text = recognizer.recognize_google(audio).lower()
                    print(f"Recognized text: {text}")

                    if "stop" in text:
                        self.speak_text("Ending the conversation. Goodbye!")
                        break

                    self.log_conversation("user", text)

                    agent_response = self.generate_agent_response(text)
                    self.speak_text(agent_response)
                    self.log_conversation("agent", agent_response)

                except sr.WaitTimeoutError:
                    print("Listening timeout. Please speak again.")
                except sr.UnknownValueError:
                    print("Could not understand the audio. Please try again.")
                except Exception as e:
                    print(f"Error in speech recognition: {e}")

    def generate_agent_response(self, user_input):
        """
        Generates a response from OpenAI's GPT API based on user input.
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_input}
                ]
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm sorry, I couldn't process your request."


    def log_conversation(self, role, message):
        """
        Logs the conversation in JSON format.
        """
        self.conversation_log.append({
            "role": role,
            "message": message
        })


assistant_id = 'assistant_id'
assistant = {
    'firstMessage': 'Hello, welcome to Real Estate Assistant! How can I assist you today?',
    'context': 'You are a virtual assistant helping customers find properties.',
    'model': 'gpt-3.5-turbo',
    'voice': 'Hinglish Speaking Lady',
    "recordingEnabled": True,
    "interruptionsEnabled": False
}

vapi = Vapi(
    api_key='api_key',
    twilio_sid='twilio_sid',
    twilio_auth_token='twilio_auth_token',
    twilio_phone_number='twilio_phone_number'
)

vapi.start(assistant_id=assistant_id)
