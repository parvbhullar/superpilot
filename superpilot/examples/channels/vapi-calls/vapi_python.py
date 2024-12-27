import pyttsx3
import time
import requests
import csv
import json
import speech_recognition as sr
from daily_call import DailyCall
from twilio.rest import Client
import openai
from daily import *

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
        if self._client:  
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
            self._client = DailyCall() 
            self._client.join(web_call_url)
            print("Successfully joined the call.")

            self.speak_text("Call successfully joined! I'm ready to assist.") 

            if outbound_numbers:
                for number in outbound_numbers:
                    self.make_outbound_call(number)

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
        if self._client:
            try:
                self._client.leave()
                print("Left the call successfully.")
            except Exception as e:
                print(f"Error stopping call: {e}")
            finally:
                self.save_conversation_log()  
                self.download_conversation_log()  
                self._client = None
                print("Client reset.")
                self.forward_call()
        else:
            print("No active call to stop.")

    def forward_call(self):
        print("Forwarding call...")
    
        try:
            forward_to_number = "+918872781496"  
            self.twilio_client.calls.create(
                to=forward_to_number,
                from_=self.twilio_phone_number,
                url=self._client.web_call_url
            )               
            print(f"Call forwarded to {forward_to_number}")
        except Exception as e:
            print(f"Error forwarding call: {e}")

    def send(self, message):
        if not self._client:
            raise Exception("Call not started. Please start the call first.")
        
        if not isinstance(message, dict) or 'type' not in message:
            raise ValueError("Invalid message format.")

        try:
            self._client.send_app_message(message)
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
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening for speech... (Say 'stop' to end)")

            user_gender = None

            while True:
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    text = recognizer.recognize_google(audio)
                    print(f"Recognized speech: {text}")

                    if user_gender is None:
                        user_gender = self.recognize_gender(audio)
                        print(f"Detected gender: {user_gender}")

                    if any(phrase in text.lower() for phrase in ["stop", "no", "not interested", "no thanks"]):
                        print("User is not interested. Disconnecting call.")
                        self.stop()
                        break

                    if "yes" in text.lower():
                        print("User is interested. Continuing communication.")

                    if "budget" in text.lower() or "lakhs" in text.lower():
                        print("Budget keyword detected in user input.")
                        budget_amount = self.extract_budget_amount(text)
                        print(f"Extracted budget amount: {budget_amount}")
                        if budget_amount < 4000000:  
                            print("Budget is less than 40 lakhs. Asking to increase budget.")
                            self.speak_text("Your budget is less than 40 lakhs. Could you please increase your budget?")
                        else:
                            print("Budget confirmed. Proceeding with details.")
                            self.speak_text("Thank you for confirming your budget. Please stay on the call while I transfer you to one of our senior representatives.")
                            self.forward_call()
                            break

                    self.append_to_transcript("user", text)
                    agent_response = self.generate_agent_response(text, user_gender)
                    print(f"Agent: {agent_response}")
                    self.append_to_transcript("agent", agent_response)

                except sr.WaitTimeoutError:
                    print("Listening timeout. Please speak again.")
                except sr.UnknownValueError:
                    print("Could not understand the audio. Please try again.")
                except sr.RequestError as e:
                    print(f"Could not request results from the speech recognition service; {e}")

    def extract_budget_amount(self, text):
        words = text.split()
        for i, word in enumerate(words):
            if word.isdigit():
                amount = int(word)
                if i+1 < len(words) and words[i+1].lower() == "lakhs":
                    return amount * 100000
                return amount
        return 0

    def recognize_gender(self, audio):
        print("Analyzing voice for gender recognition...")
        response = self.call_voice_analysis_api(audio)
        gender = response.get('gender', 'unknown')
        print(f"Detected gender: {gender}")
        return gender

    def call_voice_analysis_api(self, audio):
       
        return {'gender': 'male'}  

    def load_agent_script(self):
        script_path = "/home/dev2/projects/super-pilot/super-pilot/work/superpilot/superpilot/superpilot/examples/channels/vapi-calls/script.json"
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                agent_script = json.load(f)
            print("Agent script loaded successfully.")
            return agent_script
        except FileNotFoundError:
            print(f"Error: File not found at {script_path}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from script: {e}")
        except Exception as e:
            print(f"Unexpected error loading script: {e}")
        return []
    
    def generate_agent_response(self, user_input, user_gender):
        """
        Generate a response from the agent based on user input, gender, and script content.
        """
        interest = self.analyze_user_interest(user_input)
        if interest == "start_pitch":
            return "Hey, I'm an A.I. assistant for real estate. I can help you find the perfect property. What are you looking for?"
        elif interest == "ask_for_time_and_requirements":
            return "Sure, when would be a good time for us to discuss your property needs?"
        else:
            return "I'm here to assist you with your property inquiries. Could you please provide more details about your requirements?"
        
        
    def simulate_conversation(self):
        agent_script = self.load_agent_script()

        if not agent_script:
            print("Error: Agent script is empty or not loaded.")
            return

        for question in agent_script:
            if question['role'] == 'agent':
                print(f"Agent: {question['message']}")
                self.append_to_transcript("agent", question['message'])
                user_response = input("User: ")  
                self.append_to_transcript("user", user_response)

                agent_response = self.generate_agent_response(user_response, "unknown")  
                print(f"Agent: {agent_response}")
                self.append_to_transcript("agent", agent_response)

        transcript_json_path = "/home/dev2/projects/super-pilot/super-pilot/work/superpilot/superpilot/superpilot/examples/channels/vapi-calls/transcript.json"
        with open(transcript_json_path, "w", encoding="utf-8") as json_file:
            json.dump(self.conversation_log, json_file, ensure_ascii=False, indent=4)

        self.download_conversation_log()

    def append_to_transcript(self, role, message):
        print(f"Appending to transcript: {role}: {message}")  
        self.conversation_log.append({"role": role, "message": message})

        transcript_json_path = "/home/dev2/projects/super-pilot/super-pilot/work/superpilot/superpilot/superpilot/examples/channels/vapi-calls/transcript.json"
        with open(transcript_json_path, "w", encoding="utf-8") as json_file:
            json.dump(self.conversation_log, json_file, ensure_ascii=False, indent=4)

    def analyze_user_interest(self, user_input):
        """
        Analyze user interest based on their response.
        """
        if "yes" in user_input.lower() or "ok" in user_input.lower():
            return "start_pitch"
        elif "no" in user_input.lower():
            return "ask_for_time_and_requirements"
        else:
            return "undecided"

    

    def download_conversation_log(self):
        """
        Save the conversation log to a text file.
        """
        try:
            download_path = "/home/dev2/projects/super-pilot/conversation_download.txt"
            with open(download_path, "w", encoding="utf-8") as f:
                for entry in self.conversation_log:
                    f.write(f"{entry['role'].capitalize()}: {entry['message']}\n")
            print(f"Conversation log downloaded to {download_path}")
        except Exception as e:
            print(f"Error downloading conversation log: {e}")

assistant_id = ''

assistant = {
    'firstMessage': 'Hello, welcome to Real Estate Assistant! How can I assist you today?',
    'context': 'You are a virtual assistant helping customers find properties.',
    'model': 'gpt-3.5-turbo',
    'voice': 'Hinglish Speaking Lady',
    "recordingEnabled": True,
    "interruptionsEnabled": False
}

vapi = Vapi(
    api_key='',
    twilio_sid='',
    twilio_auth_token='',
    twilio_phone_number=''
)

script_content = vapi.load_agent_script()
print("Loaded script content:")
print(script_content)

vapi.start(assistant_id=assistant_id)

vapi.simulate_conversation()

vapi.save_conversation_log()
