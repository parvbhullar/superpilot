import gradio as gr
import re
import pyttsx3
import requests
import openai
import json
import speech_recognition as sr
from daily_call import DailyCall
from daily import *
from datetime import datetime
import threading
import time
import os
from twilio.rest import Client

class Vapi:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self, api_key=None):
        if not hasattr(self, 'initialized'):
            self.api_key = api_key
            self.api_url = "https://api.vapi.ai"
            self.openai_api_key = None
            self._client = None
            self.__app_quit = False
            self.conversation_log = []
            
            try:
                self.speaker = pyttsx3.init()
                # Configure voice properties
                self.speaker.setProperty('rate', 150)    # Speed of speech
                self.speaker.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
                voices = self.speaker.getProperty('voices')
                # Try to set a female voice if available
                for voice in voices:
                    if "female" in voice.name.lower():
                        self.speaker.setProperty('voice', voice.id)
                        break
                print("Text-to-speech engine initialized successfully")
            except Exception as e:
                print(f"Error initializing text-to-speech: {str(e)}")
                self.speaker = None
            
            self.current_call_id = None
            self.current_url = None
            
            # Initialize Twilio
            self.twilio_account_sid = ""  
            self.twilio_auth_token = ""  
            self.twilio_phone_number = ""
            self.target_phone = ""  
            try:
                self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
                print("Twilio client initialized successfully")
            except Exception as e:
                print(f"Error initializing Twilio: {str(e)}")
                self.twilio_client = None
            
            if self.openai_api_key:
                openai.api_key = self.openai_api_key
            
            self.initialized = True
            print("Vapi initialized with API key:", self.api_key)

    def start(self, *, assistant_id=None, assistant=None, assistant_overrides=None, squad_id=None, squad=None):
        print("Starting call...")
        if self._client:
            print("Stopping active call before starting a new one.")
            self.stop()

        if assistant_id:
            payload = {'assistantId': assistant_id}
        elif assistant:
            payload = {'assistant': assistant}
        elif squad_id:
            payload = {'squadId': squad_id}
        elif squad:
            payload = {'squad': squad}
        else:
            raise Exception("Error: No assistant specified.")
        
        print(f"Making API call with payload: {payload}")
        
        try:
            # Create call and store details
            call_id, web_call_url = self.create_web_call(payload)
            print(f"Received call ID: {call_id}, Web call URL: {web_call_url}")
            
            self._client = DailyCall()
            
            def on_app_message(event):
                try:
                    print(f"Raw event received: {event}")
                    if isinstance(event, str):
                        print("Processing string message...")
                        self.handle_agent_message(event)
                        return
                        
                    if isinstance(event, dict):
                        print("Processing dict message...")
                        if 'text' in event:
                            msg = event['text']
                            print(f"Found text message: {msg}")
                            self.handle_agent_message(msg)
                            return
                            
                        if 'action' in event:
                            action = event['action']
                            print(f"Found action: {action}")
                            self.append_to_transcript("agent_action", action)
                            return
                            
                        if 'data' in event:
                            print("Found data field...")
                            data = event['data']
                            if isinstance(data, dict) and 'text' in data:
                                msg = data['text']
                                print(f"Found text in data: {msg}")
                                self.handle_agent_message(msg)
                                return
                                
                        print("No recognized message format found in dict")
                        print(f"Dict keys: {event.keys()}")
                                
                    print(f"Unhandled event type: {type(event)}")
                except Exception as e:
                    print(f"Error in message handler: {str(e)}")
                    print(f"Error type: {type(e)}")
                    import traceback
                    print(f"Traceback: {traceback.format_exc()}")
                    self.append_to_transcript("error", f"Message handling error: {str(e)}")
            
            print("\nSetting up event handlers...")
            self._client.on_app_message = on_app_message
            
            print("\nJoining call...")
            self._client.join(web_call_url)
            print("Successfully joined the call")
            
            print("\nStarting conversation listener...")
            threading.Thread(target=self.listen_for_conversation, daemon=True).start()
            
            return call_id, web_call_url
            
        except Exception as e:
            print(f"Error starting call: {e}")
            raise

    def speak_text(self, text):
        """Speak the given text using text-to-speech"""
        try:
            if self.speaker is None:
                print("\nERROR: Text-to-speech not initialized")
                return
                
            print(f"\n=== SPEAKING TEXT ===")
            print(f"Text to speak: {text}")
            self.speaker.say(text)
            print("Running speech...")
            self.speaker.runAndWait()
            print("Speech completed")
        except Exception as e:
            print(f"\nERROR in text-to-speech: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

    def handle_agent_message(self, msg):
        """Handle and speak agent messages"""
        try:
            print("\n=== HANDLING AGENT MESSAGE ===")
            print(f"Original message: {msg}")
            
            self.append_to_transcript("agent", msg)
            print("Message added to transcript")
            
            clean_msg = msg.replace('*', '').replace('#', '').replace('_', '')
            print(f"Cleaned message: {clean_msg}")
            
            print("Attempting to speak message...")
            self.speak_text(clean_msg)
            print("Message handling complete")
            
        except Exception as e:
            print(f"\nERROR handling agent message: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            self.append_to_transcript("error", f"Message handling error: {str(e)}")

    def append_to_transcript(self, role, message):
        """Append a message to the conversation log"""
        timestamp = datetime.now().isoformat()
        message_obj = {
            "role": role,
            "message": message,
            "timestamp": timestamp
        }
        self.conversation_log.append(message_obj)
        self.save_transcript()
        print(f"Added to transcript - {role}: {message}")

    def save_transcript(self):
        """Save the conversation log to transcript.json"""
        transcript_path = "transcript.json"
        try:
            try:
                with open(transcript_path, 'r') as f:
                    existing_log = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_log = []
            
            with open(transcript_path, 'w') as f:
                json.dump(self.conversation_log, f, indent=4)
            print(f"Saved {len(self.conversation_log)} messages to transcript")
        except Exception as e:
            print(f"Error saving transcript: {e}")

    def stop(self):
        """Stop the current call"""
        try:
            print("Stopping call...")
            self.__app_quit = True
            if self._client:
                try:
                    self._client.leave()
                except Exception as e:
                    print(f"Error in leave: {e}")
                self._client = None
            
            self.save_transcript()
            print("Call stopped and conversation saved")
        except Exception as e:
            print(f"Error stopping call: {e}")

    def create_web_call(self, payload):
        """Create a web call with the given payload"""
        try:
            url = "https://api.vapi.ai/call/web"  
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            response = requests.post(
                url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            call_id = data.get('id')
            web_call_url = data.get('webCallUrl')
            
            if not call_id or not web_call_url:
                raise Exception("Missing call ID or URL in response")
                
            print(f"Created call - ID: {call_id}, URL: {web_call_url}")
            self.current_call_id = call_id
            self.current_url = web_call_url
            return call_id, web_call_url
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Error creating web call: {e}")
            raise

    def listen_for_conversation(self):
        """Listen for conversation using speech recognition"""
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening for speech... (Say 'stop' to end)")

            while True:
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    text = recognizer.recognize_google(audio)
                    print(f"Recognized speech: {text}")

                    if any(phrase in text.lower() for phrase in ["stop", "no", "not interested", "no thanks"]):
                        print("User wants to end the call.")
                        self.stop()
                        break

                    self.append_to_transcript("user", text)
                    print(f"User said: {text}")

                except sr.WaitTimeoutError:
                    print("Listening timeout. Please speak again.")
                except sr.UnknownValueError:
                    print("Could not understand the audio. Please try again.")
                except sr.RequestError as e:
                    print(f"Could not request results from the speech recognition service; {e}")

    def forward_call(self):
        """Forward the call to the target phone number using Twilio"""
        try:
            print("Starting call forward process...")
            print(f"Forwarding call to: {self.target_phone}")
            
            if not self.twilio_client:
                error_msg = "Twilio client not initialized"
                print(error_msg)
                self.append_to_transcript("error", error_msg)
                return error_msg
            
            print("Stopping current call...")
            self.__app_quit = True
            if self._client:
                try:
                    self._client.leave()
                except Exception as e:
                    print(f"Error in leave: {e}")
                self._client = None
            
            try:
                twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
                <Response>
                    <Say>Forwarding your call</Say>
                    <Dial>{self.target_phone}</Dial>
                </Response>"""
                
                # Create Twilio call
                call = self.twilio_client.calls.create(
                    to=self.target_phone,
                    from_=self.twilio_phone_number,
                    twiml=twiml
                )
                
                print(f"Twilio call initiated - SID: {call.sid}")
                self.append_to_transcript("system", f"Call forwarded to {self.target_phone}")
                return f"Call successfully forwarded to {self.target_phone}"
                
            except Exception as e:
                error_msg = f"Error making Twilio call: {str(e)}"
                print(error_msg)
                self.append_to_transcript("error", error_msg)
                return error_msg
            
        except Exception as e:
            error_msg = f"Error in call forwarding: {str(e)}"
            print(error_msg)
            self.append_to_transcript("error", error_msg)
            return error_msg

def start_vapi_call():
    api_key = ""
    assistant_id = ""
    vapi = Vapi(api_key=api_key)
    vapi.start(assistant_id=assistant_id)
    return "VAPI call has been started and joined successfully!"

def disconnect_vapi_call():
    vapi = Vapi(api_key="")
    vapi.stop()
    return "VAPI call has been disconnected and conversation transcript saved successfully!"

def forward_vapi_call():
    vapi = Vapi(api_key="")
    return vapi.forward_call()

#update your fronted
def launch_gradio_interface():
    with gr.Blocks() as demo:
        gr.Markdown("### VAPI Automation with Gradio")
        
        output_text = gr.Textbox(label="Output", placeholder="Status message will be displayed here", interactive=False)
        
        with gr.Row():
            start_button = gr.Button("Start Web Call")
            disconnect_button = gr.Button("Disconnect Call")
            forward_button = gr.Button("Forward Call")
        
        start_button.click(start_vapi_call, outputs=output_text)
        disconnect_button.click(disconnect_vapi_call, outputs=output_text)
        forward_button.click(forward_vapi_call, outputs=output_text)
    
    demo.launch()

launch_gradio_interface()
