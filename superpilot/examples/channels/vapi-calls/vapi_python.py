import gradio as gr
import re
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
from pymongo import MongoClient
import pyaudio
import wave
import re
from pydub import AudioSegment
import wave
import io
from bson import Binary

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
            self.contact_name = None
            self.contact_number = None
            self.audio_recording = []
            self.is_recording = False
            self.recording_thread = None
            self.CHUNK = 1024
            self.FORMAT = wave.WAVE_FORMAT_PCM
            self.CHANNELS = 2   
            self.RATE = 16000
            self.audio_dir = "recorded_conversations"
            os.makedirs(self.audio_dir, exist_ok=True)
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            print("Audio recording initialized successfully")
                
            self.user_budget = None
            self.user_profession = None
            self.user_location = None
            self.qualification_checked = False
            self.min_budget = 4000000  # 40 lakhs
            self.max_budget = 5000000  # 50 lakhs
            self.current_question = None
            self.verification_stage = 0
            
            try:
                self.mongo_client = MongoClient("mongodb://localhost:27017/")
                self.db = self.mongo_client["vapi-script"]
                self.transcript_collection = self.db["transcripts"]
                self.audio_collection = self.db["audio_recordings"]
                self.contacts_collection = self.db["contacts"]
                self.web_calls_collection = self.db["web_calls"]
                print("MongoDB connected successfully")
            except Exception as e:
                print(f"Error connecting to MongoDB: {e}")
                self.mongo_client = None
                
            self.conversation_log = []
            self.current_conversation_id = str(datetime.now().timestamp())
            
            # Initialize PyAudio
            try:
                self.audio = pyaudio.PyAudio()
                self.stream = self.audio.open(
                    format=self.FORMAT,
                    channels=self.CHANNELS,
                    rate=self.RATE,
                    input=True,
                    frames_per_buffer=self.CHUNK
                )
                print("Audio recording initialized successfully")
            except Exception as e:
                print(f"Error initializing audio: {e}")
                self.audio = None

            self.budget_attempts = 0
            self.location_attempts = 0
            self.profession_attempts = 0
            self.MAX_ATTEMPTS = 3  
            
            self.initialized = True

    def save_contact_details(self, name=None, number=None):
        """Save contact details to MongoDB"""
        try:
            if not name and not number:
                return "No contact details provided"
                
            contact_doc = {
                'name': name,
                'number': number,
                'timestamp': datetime.now(),
                'conversation_id': self.current_conversation_id
            }
            
            result = self.contacts_collection.insert_one(contact_doc)
            print(f"Contact details saved with ID: {result.inserted_id}")
            return "Contact details saved successfully"
            
        except Exception as e:
            print(f"Error saving contact details: {e}")
            return f"Error saving contact details: {str(e)}"

    def start_recording(self):
        """Start recording audio in a separate thread"""
        if self.is_recording:
            print("Already recording")
            return

        def record():
            print("Starting conversation audio recording...")
            self.audio_recording = []
            self.is_recording = True
            
            while self.is_recording:
                try:
                    data = self.stream.read(self.CHUNK)
                    self.audio_recording.append(data)

                except Exception as e:
                    print(f"Error recording audio: {e}")
                    break

            print("Conversation recording stopped")

        self.recording_thread = threading.Thread(target=record)
        self.recording_thread.start()
        print("Recording thread started")


    def stop_recording(self):
        """Stop recording audio and finalize the process"""
        if not self.is_recording:
            print("Recording is not in progress")
            return

        self.is_recording = False 
        if self.recording_thread:
            self.recording_thread.join()  
        
        self.save_audio_recording()

    def save_audio_recording(self):
        """Save the recorded audio (user and agent combined) to WAV and MP3 files and MongoDB"""
        if not self.audio_recording:
            return "No audio recording found"

        try:
            os.makedirs(self.audio_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            wav_filename = f"{self.audio_dir}/conversation_{timestamp}.wav"
            mp3_filename = f"{self.audio_dir}/conversation_{timestamp}.mp3"

            # Save as WAV first
            with wave.open(wav_filename, 'wb') as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.RATE)
                wf.writeframes(b''.join(self.audio_recording))
            print(f"Audio saved as WAV: {wav_filename}")

            # Convert to MP3
            try:
                audio = AudioSegment.from_wav(wav_filename)
                audio.export(mp3_filename, format="mp3")
                print(f"Audio converted to MP3: {mp3_filename}")

                if self.mongo_client:
                    with open(wav_filename, 'rb') as wav_file, open(mp3_filename, 'rb') as mp3_file:
                        audio_doc = {
                            'wav_data': Binary(wav_file.read()),
                            'mp3_data': Binary(mp3_file.read()),
                            'conversation_id': self.current_conversation_id,
                            'timestamp': datetime.now(),
                            'duration': len(self.audio_recording) * self.CHUNK / self.RATE,
                            'wav_filename': wav_filename,
                            'mp3_filename': mp3_filename
                        }
                        result = self.audio_collection.insert_one(audio_doc)
                        print("Audio saved to MongoDB with ID:", result.inserted_id)

            except Exception as e:
                print(f"Error converting to MP3: {e}")
                if self.mongo_client:
                    with open(wav_filename, 'rb') as wav_file:
                        audio_doc = {
                            'wav_data': Binary(wav_file.read()),
                            'conversation_id': self.current_conversation_id,
                            'timestamp': datetime.now(),
                            'duration': len(self.audio_recording) * self.CHUNK / self.RATE,
                            'wav_filename': wav_filename
                        }
                        result = self.audio_collection.insert_one(audio_doc)
                        print("WAV audio saved to MongoDB with ID:", result.inserted_id)

        except Exception as e:
            print(f"Error saving audio: {e}")
            return f"Error saving audio: {str(e)}"

        return "Audio saved successfully"

    def record_audio(self):
        """Continuously record audio chunks"""
        print("Started audio recording thread")
        while self.is_recording:
            try:
                if self.stream:
                    data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                    self.audio_recording.append(data)

            except Exception as e:
                print(f"Error recording audio chunk: {e}")
                break
        print("Audio recording thread stopped")

    def start_qualification_process(self):
        """Start the qualification process with initial greeting"""
        self.verification_stage = 0
        self.append_to_transcript("agent", "Hello! I'm calling regarding premium properties in Chandigarh. What is your budget for the property?")
        self.verification_stage = 1
        self.current_question = "budget"

    def handle_agent_message(self, msg):
        """Handle agent messages without text-to-speech"""
        try:
            print("\n=== HANDLING AGENT MESSAGE ===")
            print(f"Original message: {msg}")
            
            self.append_to_transcript("agent", msg)
            print("Message added to transcript")
            
        except Exception as e:
            print(f"\nERROR handling agent message: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            self.append_to_transcript("error", f"Message handling error: {str(e)}")

    def disconnect_call(self, reason=""):
        """Disconnect the call with a reason"""
        try:
            print(f"Disconnecting call: {reason}")
            self.append_to_transcript("system", f"Call disconnected: {reason}")
            
            if self._client:
                try:
                    self._client.leave()
                except Exception as e:
                    print(f"Error in leave: {e}")
                finally:
                    self._client = None
            
            self.stop_recording()
            self.save_transcript()
            self.__app_quit = True
            
        except Exception as e:
            print(f"Error disconnecting call: {e}")

    def append_to_transcript(self, role, message):
        """Append a message to the conversation log and MongoDB"""
        try:
            message_obj = {
                "conversation_id": self.current_conversation_id,
                "role": role,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "call_id": self.current_call_id
            }

            formatted_message = {
                "role": role,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }

            self.conversation_log.append(formatted_message)

            if self.mongo_client:
                try:
                    self.transcript_collection.insert_one(message_obj)
                    print(f"Message saved to MongoDB - {role}: {message}")
                except Exception as e:
                    print(f"Error saving to MongoDB: {e}")

            self.save_transcript()
            
            print(f"Added to transcript - {role}: {message}")
            return formatted_message

        except Exception as e:
            print(f"Error in append_to_transcript: {e}")
            return None

    def save_transcript(self):
        """Save the conversation log to transcript.json"""
        try:
            transcript_path = "transcript.json"
            
            with open(transcript_path, 'w') as f:
                json.dump(self.conversation_log, f, indent=4)
            print(f"Saved {len(self.conversation_log)} messages to transcript.json")
            
        except Exception as e:
            print(f"Error saving transcript: {e}")

    def handle_user_message(self, message):
        """Handle incoming user message with sequential qualification checks"""
        try:
            self.append_to_transcript("user", message)
            
            if self.verification_stage == 0:
                self.append_to_transcript("agent", "Before we start, may I have your permission to ask a few questions about your property preferences?")
                self.current_question = "permission"
                return
            
            if self.current_question == "permission":
                if "no" in message.lower():
                    self.append_to_transcript("agent", "Apka shukriya! We appreciate your time. Have a great day!")
                    self.disconnect_call("User declined permission")
                    return
                elif "yes" in message.lower():
                    self.start_qualification_process()
                    return
                else:
                    self.append_to_transcript("agent", "Could you please respond with yes or no regarding my question?")
                    return

            if self.current_question == "budget":
                budget = self.extract_budget_from_text(message)
                if budget:
                    self.user_budget = budget
                    if budget < self.min_budget:
                        self.append_to_transcript("agent", "I apologize, but your budget is below our minimum requirement of 40 lakhs. We will contact you when we have properties in your budget range. Thank you for your time.")
                        self.disconnect_call("Budget below minimum requirement")
                        return
                    
                    self.verification_stage = 2
                    self.current_question = "location"
                    self.append_to_transcript("agent", "Are you looking for property in Chandigarh?")
                else:
                    self.budget_attempts += 1
                    if self.budget_attempts >= self.MAX_ATTEMPTS:
                        self.append_to_transcript("agent", "I apologize, but I'm having trouble understanding your budget. Please contact us back when you have a specific budget in mind. Thank you for your time.")
                        self.disconnect_call("Unable to determine budget after multiple attempts")
                        return
                    self.append_to_transcript("agent", "Could you please specify your budget clearly in lakhs? For example, '45 lakhs' or '50 lakhs'.")
                    
            elif self.current_question == "location":
                if self.check_location(message):
                    self.user_location = "Chandigarh"
                    self.verification_stage = 3
                    self.current_question = "profession"
                    self.append_to_transcript("agent", "Do you work in an IT company? What is your profession?")
                else:
                    self.location_attempts += 1
                    if self.location_attempts >= self.MAX_ATTEMPTS:
                        self.append_to_transcript("agent", "I apologize, but we currently only have properties in Chandigarh. We will contact you when we expand to other areas. Thank you for your time.")
                        self.disconnect_call("Location not in Chandigarh after multiple attempts")
                        return
                    self.append_to_transcript("agent", "I need to confirm if you're looking for property in Chandigarh. Please answer yes or no.")
                    
            elif self.current_question == "profession":
                if self.check_profession(message):
                    self.user_profession = "IT"
                    self.verification_stage = 4
                    self.current_question = "qualified"
                    self.append_to_transcript("agent", "Perfect! You qualify for our premium properties. Let me tell you about our offerings.")
                else:
                    self.profession_attempts += 1
                    if self.profession_attempts >= self.MAX_ATTEMPTS:
                        self.append_to_transcript("agent", "I apologize, but this property is specifically for IT professionals. We will contact you when we have suitable options for other professions. Thank you for your time.")
                        self.disconnect_call("Not in IT profession after multiple attempts")
                        return
                    self.append_to_transcript("agent", "Could you please specify if you work in the IT sector and what your role is?")
            
            print(f"Processing user message: {message}")
            
        except Exception as e:
            print(f"Error handling user message: {e}")
            self.append_to_transcript("error", f"Error handling message: {str(e)}")


    def start(self, *, assistant_id=None, assistant=None, assistant_overrides=None, squad_id=None, squad=None):
        """Start a VAPI call with proper error handling"""
        print("Starting call...")
        if self._client:
            print("Client already exists")
            return None, None
        
        self.start_recording()
        
        try:
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
            
            call_id, web_call_url = self.create_web_call(payload)
            if not call_id or not web_call_url:
                raise Exception("Failed to get valid call ID or URL")
                
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
            if not web_call_url:
                raise Exception("No valid web call URL")
            self._client.join(web_call_url)
            print("Successfully joined the call")
            
            print("\nStarting conversation listener...")
            threading.Thread(target=self.listen_for_conversation, daemon=True).start()
            
            self.start_qualification_process()
            
            return call_id, web_call_url
            
        except Exception as e:
            print(f"Error in start: {str(e)}")
            self.stop_recording() 
            if self._client:
                try:
                    self._client.leave()
                except:
                    pass
                self._client = None
            return None, None

    def stop(self):
        """Stop the current call and save all recordings"""
        try:
            print("Stopping call...")
            self.__app_quit = True
            
            if self.is_recording:  
                print("Stopping audio recording...")
                self.stop_recording()
                self.save_audio_recording()  
            if self._client:
                try:
                    self._client.leave()
                    print("Successfully left the call.")
                except Exception as e:
                    print(f"Error leaving call: {e}")
                finally:
                    self._client = None
            
            self.save_transcript()
            print("Call stopped, conversation and audio saved.")
            
        except Exception as e:
            print(f"Error stopping call: {e}")


    def create_web_call(self, payload):
        """Create a web call with the given payload."""
        try:
            url = f"{self.api_url}/call/web"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            call_id = data.get('id')
            web_call_url = data.get('webCallUrl')

            if not call_id or not web_call_url:
                raise Exception("Missing call ID or URL in response.")
            
            web_call_doc = {
                'call_id': call_id,
                'web_call_url': web_call_url,
                'timestamp': datetime.now(),
                'conversation_id': self.current_conversation_id,
                'contact_name': self.contact_name,
                'contact_number': self.contact_number,
                'payload': payload,
                'response': data
            }
            
            if self.mongo_client:
                try:
                    result = self.web_calls_collection.insert_one(web_call_doc)
                    print(f"Web call details saved with ID: {result.inserted_id}")
                except Exception as e:
                    print(f"Error saving web call details: {e}")
            
            self.current_call_id = call_id
            self.current_url = web_call_url
            return call_id, web_call_url
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            return None, None
        except Exception as e:
            print(f"Error creating web call: {e}")
            return None, None

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

                    self.handle_user_message(text)
                    print(f"User said: {text}")

                except sr.WaitTimeoutError:
                    print("Listening timeout. Please speak again.")
                except sr.UnknownValueError:
                    print("Could not understand the audio. Please try again.")
                except sr.RequestError as e:
                    print(f"Could not request results from the speech recognition service; {e}")

    def extract_budget_from_text(self, text):
        """Extract budget amount from text"""
        text = text.lower()
        match = re.search(r'(\d+)(?:\s*(?:lakh|lac|l|lakhs)s?)', text)
        if match:
            return float(match.group(1)) * 100000  
        
        match = re.search(r'(\d+(?:\.\d+)?)(?:\s*(?:cr|crore|crores))', text)
        if match:
            return float(match.group(1)) * 10000000  # Convert crores to rupees
            
        match = re.search(r'(\d+)', text)
        if match:
            return float(match.group(1)) * 100000
            
        return None


    def handle_user_budget(self, message):
        """Handle user budget input"""
        budget = self.extract_budget_from_text(message)
        
        if budget is not None:
            self.user_budget = budget
            if self.user_budget < self.min_budget:
                response_message = "Apke budget ke anusar property khoj kr apko call back krwati hu."
                print(response_message)  
                self.disconnect_call() 
                return response_message

            print(f"User's budget is {self.user_budget}, which is within acceptable limits.")
            return "Thank you for providing your budget."

        return "Could not extract a valid budget from your message."

    def check_location(self, text):
        """Check if location is Chandigarh"""
        text = text.lower()
        return 'chandigarh' in text

    def check_profession(self, text):
        """Check if user is in IT company"""
        text = text.lower()
        it_keywords = ['it', 'software', 'tech', 'developer', 'engineer', 'programmer', 'analyst', 'consultant']
        return any(keyword in text for keyword in it_keywords)

    def forward_call(self, target_agent_id):
        """Forward the current call to another agent"""
        if not self._client or not self.current_call_id:
            return "No active call to forward"
            
        try:
            url = f"{self.api_url}/call/{self.current_call_id}/forward"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            payload = {
                'assistantId': target_agent_id
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            if self.mongo_client:
                forward_doc = {
                    'original_call_id': self.current_call_id,
                    'target_agent_id': target_agent_id,
                    'timestamp': datetime.now(),
                    'conversation_id': self.current_conversation_id
                }
                self.web_calls_collection.insert_one(forward_doc)
            
            return "Call forwarded successfully"
            
        except Exception as e:
            print(f"Error forwarding call: {e}")
            return f"Error forwarding call: {str(e)}"

def save_contact_number(self, contact_number):
        """Save the contact number to MongoDB."""
        if contact_number:
            contact_doc = {
                'contact_number': contact_number,
                'timestamp': datetime.now()
            }
            try:
                self.contacts_collection.insert_one(contact_doc) 
                return "Contact number saved successfully."
            except Exception as e:
                return f"Error saving contact number: {e}"
        return "No contact number provided."

def start_vapi_call(selected_agent, contact_name=None, contact_number=None):
    """Start a VAPI call with selected agent"""
    try:
        if not selected_agent:
            return "Please select an agent first"
            
        agent_id = selected_agent.split(" ")[0].strip()
        print(f"Starting call with agent ID: {agent_id}")
        
        vapi = Vapi(api_key="")
        
        vapi.contact_name = contact_name
        vapi.contact_number = contact_number
        vapi.save_contact_details(contact_name, contact_number)
        
        call_id, web_call_url = vapi.start(assistant_id=agent_id)
        
        if call_id and web_call_url:
            return f"Call started successfully with agent {selected_agent}"
        else:
            return "Failed to start call. Please try again."
            
    except Exception as e:
        print(f"Error in start_vapi_call: {str(e)}")
        return f"Error starting call: {str(e)}"

def disconnect_vapi_call():
    """Disconnect the VAPI call and save recordings"""
    try:
        vapi = Vapi(api_key="")
        vapi.stop()
        return "Call disconnected and recordings saved successfully!"
    except Exception as e:
        return f"Error disconnecting call: {str(e)}"

def forward_vapi_call(target_agent):
    """Forward the current VAPI call to another agent"""
    try:
        if not target_agent:
            return "Please select a target agent first"
            
        target_agent_id = target_agent.split(" ")[0].strip()
        
        vapi = Vapi(api_key="")
        result = vapi.forward_call(target_agent_id)
        
        return result
        
    except Exception as e:
        print(f"Error in forward_vapi_call: {str(e)}")
        return f"Error forwarding call: {str(e)}"

def launch_gradio_interface():
    """Launch the Gradio interface for VAPI calls"""
    with gr.Blocks() as demo:
        gr.Markdown("# VAPI Call Interface")
        
        output_text = gr.Textbox(
            label="Status",
            placeholder="Call status will appear here...",
            interactive=False
        )
        
        agent_selector = gr.Dropdown(
            choices=[
                " Anchal Hindi",
                "Anchal English"
            ],
            label="Select Agent",
            value=" Anchal Hindi",
            interactive=True
        )
        
        forward_agent_selector = gr.Dropdown(
            choices=[
                " Anchal Hindi",
                "Anchal English"
            ],
            label="Forward to Agent",
            value="Anchal English",
            visible=True,
            interactive=True
        )
        
        contact_name = gr.Textbox(
            label="Contact Name",
            placeholder="Enter contact name",
            interactive=True
        )
        
        contact_number = gr.Textbox(
            label="Contact Number",
            placeholder="Enter contact number",
            interactive=True
        )
        
        with gr.Row():
            start_button = gr.Button("Start Call", variant="primary")
            disconnect_button = gr.Button("Disconnect", variant="stop")
            forward_button = gr.Button("Forward Call", variant="secondary")
        
        start_button.click(
            fn=start_vapi_call,
            inputs=[agent_selector, contact_name, contact_number],
            outputs=output_text,
            api_name="start_call"
        )
        
        disconnect_button.click(
            fn=disconnect_vapi_call,
            inputs=None,
            outputs=output_text,
            api_name="disconnect_call"
        )
        
        forward_button.click(
            fn=forward_vapi_call,
            inputs=forward_agent_selector,
            outputs=output_text,
            api_name="forward_call"
        )
    
    demo.launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    launch_gradio_interface()
