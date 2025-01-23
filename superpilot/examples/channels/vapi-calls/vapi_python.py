import os
import json
import time
import threading
import requests
import pandas as pd
import gradio as gr
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from daily_call import DailyCall
from daily import *
# from speech_recognition as sr
import pyaudio
import wave
import re
from pydub import AudioSegment
import wave
import io
from bson import Binary
import random
import openai
import speech_recognition as sr
import pyaudio
import wave
import re
from pydub import AudioSegment
import wave
import io
from bson import Binary
import pandas as pd
import random
from dotenv import load_dotenv
import os
import websockets
import asyncio
import base64

# Load environment variables
load_dotenv()

# MongoDB Connection
MONGODB_URI = "mongodb://localhost:27017/"
MONGODB_DB = "vapi-script"

def get_mongodb_connection():
    """Get MongoDB connection"""
    try:
        client = MongoClient(MONGODB_URI)
        db = client[MONGODB_DB]
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {str(e)}")
        return None

def save_transcript_to_mongodb(call_id, agent_id, customer_name, customer_number, transcript_data):
    """Save transcript to MongoDB"""
    try:
        db = get_mongodb_connection()
        if not db:
            return False

        # Create call record
        call_record = {
            'call_id': call_id,
            'agent_id': agent_id,
            'customer_name': customer_name,
            'customer_number': customer_number,
            'timestamp': datetime.now(),
            'transcript': transcript_data,
            'status': 'completed'
        }

        # Update or insert into MongoDB
        result = db.calls.update_one(
            {'call_id': call_id},
            {'$set': call_record},
            upsert=True
        )
        print(f"Transcript saved to MongoDB with ID: {result.upserted_id if result.upserted_id else call_id}")
        return True
    except Exception as e:
        print(f"Error saving to MongoDB: {str(e)}")
        return False

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
            
            self.conversation_vocabulary = {
                'greetings': {
                    'hello': 'नमस्ते',
                    'welcome': 'स्वागत है',
                    'thank you': 'धन्यवाद'
                },
                'property_terms': {
                    'budget': 'बजट',
                    'property': 'प्रॉपर्टी',
                    'location': 'स्थान',
                    'size': 'आकार',
                    'price': 'कीमत',
                    'land': 'जमीन',
                    'area': 'क्षेत्र'
                },
                'responses': {
                    'yes': 'हाँ',
                    'no': 'नहीं',
                    'great': 'बहुत अच्छा',
                    'excellent': 'उत्कृष्ट'
                }
            }
            
            self.translations = {}
            for category in self.conversation_vocabulary.values():
                self.translations.update({v: k for k, v in category.items()})
            
            self.agent_vocabulary = self.load_agent_vocabulary()
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
                print(f"MongoDB connection note: {e}")
                self.mongo_client = None

            self.conversation_log = []
            self.current_conversation_id = str(datetime.now().timestamp())

            self.budget_attempts = 0
            self.location_attempts = 0
            self.profession_attempts = 0
            self.MAX_ATTEMPTS = 3 

            self.initialized = True

    def load_agent_vocabulary(self):
        """Load bilingual vocabulary from CSV"""
        csv_path = "/home/dev2/projects/super-pilot/super-pilot/work/superpilot/superpilot/superpilot/examples/channels/vapi-calls/Hinglish Vocab - Hinglish Vocab.csv"
        
        vocabulary = {}
        df = pd.read_csv(csv_path)
        
        for _, row in df.iterrows():
            english = row['अंग्रेज़ी शब्द']
            hindi = row['हिंदी शब्द']
            vocabulary[english] = hindi
        
        self.translations = {v: k for k, v in vocabulary.items()}
        
        print("Vocabulary loaded successfully from CSV")
        return vocabulary


    def enhance_agent_message(self, message):
        """Replace Hindi terms with bilingual pairs"""
        enhanced_message = message
        for hindi_word, english_word in self.translations.items():
            if hindi_word in message:
                enhanced_message = enhanced_message.replace(hindi_word, f"{english_word} ({hindi_word})")
        return enhanced_message

    def translate_text(self, text):
        """Enhance text with bilingual vocabulary"""
        if not text:
            return text
        translated = text
        for hindi, english in self.translations.items():
            translated = translated.replace(hindi, f"{english} ({hindi})")
        
        print(f"Enhanced bilingual text: {translated}")
        return translated

        
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

            with wave.open(wav_filename, 'wb') as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.RATE)
                wf.writeframes(b''.join(self.audio_recording))
            print(f"Audio saved as WAV: {wav_filename}")

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
        prompts = [
            f"May I discuss some Property Type ({self.agent_vocabulary['Property Type']}) options with you?",
            f"Please share your Name ({self.agent_vocabulary['Name']}) for our records.",
            f"What's your Budget ({self.agent_vocabulary['Budget']}) range for the property?",
            f"What Land Size ({self.agent_vocabulary['Land Size']}) are you looking for?",
            f"Which Area ({self.agent_vocabulary['Area']}) interests you?"
        ]
        
        self.verification_stage = 1
        self.append_to_transcript("agent", prompts[0])
        self.current_question = "permission"



    def handle_agent_message(self, msg):
        try:
            print("\n=== HANDLING AGENT MESSAGE ===")
            
            context = "greetings"
            if "budget" in msg.lower() or "price" in msg.lower():
                context = "property_terms"
            elif "location" in msg.lower() or "area" in msg.lower():
                context = "property_terms"
            
            words = msg.split()
            enhanced_words = []
            for word in words:
                if word in self.translations:
                    english_word = self.translations[word]
                    enhanced_words.append(f"{english_word} ({word})")
                else:
                    enhanced_words.append(word)
            
            enhanced_msg = " ".join(enhanced_words)
            print(f"Enhanced bilingual message: {enhanced_msg}")
            
            self.append_to_transcript("agent_original", msg)
            self.append_to_transcript("agent_enhanced", enhanced_msg)
            
        except Exception as e:
            print(f"Message enhancement note: {e}")
            self.append_to_transcript("agent", msg)


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
        """Handle incoming user message with professional responses"""
        translated_message = self.translate_text(message)
        print(f"Original message: {message}")
        print(f"Translated message: {translated_message}")

        self.append_to_transcript("user_original", message)
        self.append_to_transcript("user_translated", translated_message)

        # Initial welcome
        if self.verification_stage == 0:
            welcome_msg = "Welcome! I'm excited to help you find your dream Property (प्रॉपर्टी). Would you like to explore our premium options?"
            self.append_to_transcript("agent", welcome_msg)
            self.current_question = "permission"
            return

        # Handle permission
        if self.current_question == "permission":
            if "no" in translated_message.lower():
                self.append_to_transcript("agent", "Thank you for your interest! Feel free to reach out when you'd like to explore our premium Properties (प्रॉपर्टी).")
                self.disconnect_call("User chose to explore later")
                return
            if "yes" in translated_message.lower():
                self.start_qualification_process()
                return
            self.append_to_transcript("agent", "Great! A simple yes will help us start finding your perfect Property (प्रॉपर्टी).")
            return

        if self.current_question == "budget":
            budget = self.extract_budget_from_text(translated_message)
            if budget:
                self.user_budget = budget
                if self.user_budget < self.min_budget:
                    self.append_to_transcript("agent", "Apke budget ke anusar property khoj kr apko call back krwati hu.")
                    self.disconnect_call()  
                    return

                print(f"User's budget is {self.user_budget}, which is within acceptable limits.")
                return "Thank you for providing your budget."

            return "Could not extract a valid budget from your message."

        elif self.current_question == "location":
            if self.check_location(translated_message):
                self.user_location = "Chandigarh"
                self.verification_stage = 2
                self.current_question = "profession"
                self.append_to_transcript("agent", "Wonderful choice! Chandigarh (चंडीगढ़) has excellent Properties (प्रॉपर्टी). What's your Profession (पेशा)? Are you in the IT sector?")
            else:
                self.location_attempts += 1
                if self.location_attempts >= self.MAX_ATTEMPTS:
                    self.location_attempts = 0 
                    self.append_to_transcript("agent", "Let's focus on Chandigarh (चंडीगढ़) - it's where our premium Properties (प्रॉपर्टी) are located. Would you like to explore options here?")
                else:
                    self.append_to_transcript("agent", "Are you interested in Properties (प्रॉपर्टी) in Chandigarh (चंडीगढ़)? A simple yes or no will help.")

        elif self.current_question == "profession":
            if self.check_profession(translated_message):
                self.user_profession = "IT"
                self.verification_stage = 3
                self.current_question = "qualified"
                self.append_to_transcript("agent", "Perfect match! You'll love our premium Properties (प्रॉपर्टी). Let me share some exciting options with you!")
            else:
                self.profession_attempts += 1
                if self.profession_attempts >= self.MAX_ATTEMPTS:
                    self.profession_attempts = 0 
                    self.append_to_transcript("agent", "Tell me more about your work in the IT sector - we have special offers for IT professionals!")
                else:
                    self.append_to_transcript("agent", "Do you work in the IT sector? What's your role?")

        print(f"Processing user message: {message}")


    def start_vapi_call(agent, name, number, mailing_address, source_name=""):
        """
        Start a dynamic VAPI call that adjusts based on user input for name, phone number, grade, etc.
        The conversation with VAPI AI should be dynamic, asking the user for various pieces of information.

        Parameters:
        - agent: Name of the agent initiating the call.
        """
        try:
            if not all([agent, name, number, mailing_address]):
                return "Please provide all required information."

            formatted_number = format_phone_number(number)
            if not formatted_number:
                return "Invalid phone number format."

            agent_id = get_agent_id(agent)
            if not agent_id:
                return f"Agent {agent} not found."

            location = mailing_address.split(',')[1].strip() if ',' in mailing_address else mailing_address.strip()

            # Define the conversation flow with dynamic prompts, including course details
            conversation_flow = {
                "introduction_phase": {
                    "greeting": {
                        "initial": f"Before we proceed, am I speaking with {name}?",
                        "wait_for_confirmation": True,
                        "introduction": f"Thank you! I'm {agent} from CuriousKid. I see you registered on our website through Instagram and expressed interest in our Robotics and AI courses. Do you remember the registration? I wanted to talk to you about supporting your child's STEM learning journey. Do you have a little time?",
                        "wait_for_time_confirmation": True
                    },
                    "identity_confirmation": {
                        "confirmed": f"Great, thank you for confirming, {name}!",
                        "no_response": f"Just to confirm, is this {name}?",
                        "still_unclear": f"Sorry for the confusion, just to double-check, is your name {name}?",
                        "final_confirmation": "Awesome, thank you for confirming!",
                        "acknowledgment": f"That's wonderful, {name}! I'll be happy to assist you in getting more details about our programs and setting up a session for your child."
                    }
                },
                "student_details": {
                    "gather_info": {
                        "ask_details": "Please tell me your child's name and their grade?",
                        "wait_for_response": True,
                        "age_verification": "Based on their grade, [child_name] would approximately be around [age] years. Is that right?",
                        "wait_for_age_confirmation": True
                    },
                    "location_verification": {
                        "confirm_location": f"May I confirm your current location? Is it {location}?",
                        "wait_for_location": True,
                        "tech_access": "Does [child_name] have access to a laptop and a stable internet connection for the sessions?",
                        "wait_for_tech_confirmation": True
                    }
                },
                "parent_information": {
                    "profession": {
                        "primary": "If I may ask, what do you do for a living?",
                        "wait_for_primary": True,
                        "secondary": "Could you also share what your husband does professionally?",
                        "wait_for_secondary": True
                    },
                    "motivation": "I believe you've seen our advertisement on emerging technologies like robotics and artificial intelligence. Could you share what motivated you to register [child_name]?"
                },
                "company_overview": {
                    "introduction": f"That's fantastic to hear, {name}! CuriousKid is India's largest innovation training company, specializing in teaching kids advanced technologies like electronics, robotics, artificial intelligence, and entrepreneurship. Did you know that kids aged 8 to 16 years have achieved over 170 Patents through our programs? It's truly inspiring!",
                },
                "course_intro": {
                    "grade_query": "Now, based on [Child's Name]'s grade, let me tell you about our most suitable program.",
                    "little_innovator": {
                        "grades": [1, 2],
                        "overview": "For grades 1-2, we have our Little Innovator Program. This is specially designed as an entry-level course focusing on foundational skills.",
                        "content": [
                            "Introduction to basic coding concepts",
                            "Hands-on robotics projects",
                            "Fun electronics activities that encourage creativity"
                        ],
                        "class_structure": "Classes are held twice a week in small groups of up to 10 students.",
                        "trainer_credentials": "Our instructors are alumni from prestigious institutions with experience in teaching young learners.",
                        "program_benefits": "The program focuses on cognitive development, creativity, problem-solving skills, and teamwork.",
                        "fee_structure": "Each module is priced at eighteen thousand rupees."
                    },
                    "emerging_tech_course": {
                        "grades": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                        "overview": "For grade 3 and above, we offer our comprehensive Emerging Tech Course with five specialized modules.",
                        "modules": [
                            "Electronics: Understanding circuits and components through practical exercises.",
                            "Embedded Design and Robotics: Building robots with sensors and microcontrollers.",
                            "Internet of Things (IoT): Learning device connectivity.",
                            "Artificial Intelligence: Basics of AI concepts and machine learning.",
                            "Entrepreneurship: Innovation and business skills development."
                        ],
                        "class_structure": "Classes are held twice a week in small groups.",
                        "trainer_credentials": "Our instructors are graduates from top engineering colleges with expertise in their fields.",
                        "program_benefits": "The program prepares students for future challenges with focus on creativity, critical thinking, and practical skills.",
                        "fee_structure": "Each module is priced at twenty-four thousand rupees."
                    }
                },
                "diagnostic_session": {
                    "offer": "We offer a free diagnostic session to explore your child's interests through engaging experiments. Would you like to schedule this session today?",
                    "scheduling": {
                        "ask_time": "What date and time would work best for you to schedule this session? We are available at various times throughout the week.",
                        "confirmation": "Great! I've scheduled the session for [time] on [date]. You'll receive a call from our STEM expert shortly for confirmation."
                    }
                },
                "closing": {
                    "farewell": f"Thank you for your time, {name}! If you have any questions or need further assistance, please don't hesitate to reach out. Have a great day!"
                }
            }

            # Create dynamic context with extracted information
            initial_context = {
                "customer_info": {
                    "name": name,
                    "phone": formatted_number,
                    "mailing_address": mailing_address,
                    "location": location
                },
                "agent_info": {
                    "name": agent
                },
                "conversation_flow": conversation_flow,
                "metadata": {
                    "current_time": "2025-01-20T18:27:45+05:30",
                    "source": "Instagram",
                    "registration_type": "website"
                }
            }

            # Prepare the payload for API request
            call_payload = {
                'assistantId': agent_id,
                'phoneNumberId': VAPI_PHONE_NUMBER_ID,
                'customer': {
                    'name': name,
                    'number': formatted_number
                },
                'metadata': {
                    'name': name,
                    'mailing_address': mailing_address,
                    'location': location,
                    'agent_name': agent,
                    'source': 'Instagram'
                },
                'assistantOverrides': {
                    'variableValues': {
                        'name': name,
                        'mailing_address': mailing_address,
                        'location': location,
                        'agent_name': agent
                    },
                    'context': json.dumps(initial_context)
                }
            }

            # Log information for debugging
            print(f"Making call to {formatted_number}")
            print(f"Using agent ID: {agent_id}")
            print(f"Call payload: {json.dumps(call_payload, indent=2)}")

            # Make the API call to initiate the VAPI session
            response = requests.post(
                'https://api.vapi.ai/call/phone',
                headers={
                    'Authorization': f'Bearer {auth_token}',
                    'Content-Type': 'application/json'
                },
                json=call_payload
            )

            if response.status_code in [200, 201]:
                call_data = response.json()
                call_id = call_data.get('id')

                # Start recording the call (Make sure this function is defined)
                start_call_recording(call_id, agent_id, name, formatted_number)

                # Start a thread to poll for call status
                polling_thread = threading.Thread(
                    target=poll_call_status,
                    args=(call_id, agent_id, name, formatted_number, {
                        'Authorization': f'Bearer {auth_token}',
                        'Content-Type': 'application/json'
                    })
                )
                polling_thread.daemon = True
                polling_thread.start()

                return f"Started call for {name} with phone number {formatted_number}."
            else:
                return f"Failed to start call: {response.text}"

        except Exception as e:
            return f"Error starting call: {str(e)}"

    def send_vapi_request(auth_token, payload, prompt):
        """Send a request to VAPI with a specific prompt."""
        try:
            payload['assistantOverrides']['context'] = json.dumps({"prompt": prompt})
            response = requests.post(
                'https://api.vapi.ai/call/phone',
                headers={
                    'Authorization': f'Bearer {auth_token}',
                    'Content-Type': 'application/json'
                },
                json=payload
            )
            if response.status_code in [200, 201]:
                print(f"Prompt sent: {prompt}")
                return response.json()
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error in send_vapi_request: {str(e)}")
            return None

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
            
            # Save transcript
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
            
            # Make API request
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
            return float(match.group(1)) * 10000000  
            
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

    def save_remarks(self, csv_data, remarks_text):
        """Save CSV data and remarks to MongoDB"""
        try:
            csv_dict = csv_data.to_dict('records')
            
            doc = {
                'csv_data': csv_dict,
                'remarks': remarks_text,
                'timestamp': datetime.now(),
                'conversation_id': self.current_conversation_id
            }
            
            if self.mongo_client:
                remarks_collection = self.db['remarks']
                result = remarks_collection.insert_one(doc)
                print(f"Remarks and CSV data saved with ID: {result.inserted_id}")
                return str(result.inserted_id)
            return None
            
        except Exception as e:
            print(f"Error saving remarks and CSV: {e}")
            return None

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


def extract_messages(self, transcript_json):
    """
    Extract user and agent messages from VAPI transcript
    """
    messages = []
    try:
        if isinstance(transcript_json, str):
            transcript_data = json.loads(transcript_json)
        else:
            transcript_data = transcript_json

        for message in transcript_data.get("messages", []):
            role = message.get("role", "")
            content = message.get("content", "")
            timestamp = message.get("timestamp", "")
            
            if role and content:
                messages.append({
                    "role": role,
                    "content": content,
                    "timestamp": timestamp
                })
    except Exception as e:
        print(f"Error extracting messages: {str(e)}")
    
    return messages

def generate_readable_transcript(self, messages, output_format="txt"):
    """
    Generate a readable transcript from extracted messages
    """
    if not messages:
        return "No messages found in transcript"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if output_format == "txt":
        output = f"Conversation Transcript (Generated at {timestamp})\n"
        output += "=" * 50 + "\n\n"
        
        for msg in messages:
            role = msg["role"].capitalize()
            content = msg["content"]
            msg_time = msg.get("timestamp", "")
            
            output += f"{role}: {content}\n"
            if msg_time:
                output += f"Time: {msg_time}\n"
            output += "-" * 30 + "\n"
        
        filename = f"transcript_{timestamp}.txt"
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(output)
        
        return filepath
    
    elif output_format == "json":
        output = {
            "generated_at": timestamp,
            "messages": messages
        }
        
        filename = f"transcript_{timestamp}.json"
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        
        return filepath

def save_transcript(call_id, messages):
    """Save the transcript of the conversation to JSON, TXT formats and MongoDB"""
    try:
        timestamp = datetime.now().isoformat()
        
        transcript = {
            'call_id': call_id,
            'timestamp': timestamp,
            'messages': messages
        }
        
        # 1. Save/Append to transcript.json
        existing_transcripts = []
        try:
            if os.path.exists('transcript.json'):
                with open('transcript.json', 'r') as f:
                    existing_data = json.load(f)
                    if isinstance(existing_data, list):
                        existing_transcripts = existing_data
                    elif isinstance(existing_data, dict):
                        existing_transcripts = [existing_data]
        except Exception as e:
            print(f"Error reading existing transcript.json: {str(e)}")
        
        # Add new transcript
        existing_transcripts.append(transcript)
        
        # Save updated transcripts
        with open('transcript.json', 'w') as f:
            json.dump(existing_transcripts, f, indent=2)
            
        # 2. Save to MongoDB
        try:
            if hasattr(Vapi._instance, 'transcript_collection') and Vapi._instance.transcript_collection:
                Vapi._instance.transcript_collection.insert_one({
                    'call_id': call_id,
                    'timestamp': timestamp,
                    'messages': messages
                })
                print(f"Transcript saved to MongoDB for call {call_id}")
        except Exception as e:
            print(f"Error saving to MongoDB: {str(e)}")
            
        # 3. Use TranscriptExtractor to generate readable formats
        extractor = TranscriptExtractor()
        txt_output = extractor.generate_readable_transcript(messages, call_id, "txt")
        json_output = extractor.generate_readable_transcript(messages, call_id, "json")
        print(f"Generated transcript files: \nTXT: {txt_output}\nJSON: {json_output}")
        
        print(f"Transcript saved successfully for call {call_id}")
        print(f"Generated TXT transcript: {txt_output}")
        print(f"Generated JSON transcript: {json_output}")
        
    except Exception as e:
        print(f"Error saving transcript: {str(e)}")

def disconnect_vapi_call():
    """Disconnect the current VAPI call"""
    try:
        global current_call_id
        if not current_call_id:
            return "No active call to disconnect"
            
        auth_token = os.getenv('VAPI_AUTH_TOKEN')
        if not auth_token:
            return "Missing VAPI credentials in environment variables"
            
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f'https://api.vapi.ai/call/{current_call_id}/hangup',
            headers=headers
        )
        
        if response.status_code in [200, 201]:
            current_call_id = None
            return "Call disconnected successfully. Conversation was successful."
        else:
            error_msg = f"Failed to disconnect call: {response.text}"
            print(error_msg)
            return error_msg
            
    except Exception as e:
        return f"Error disconnecting call: {str(e)}"

def forward_vapi_call(target_agent):
    """Forward the current VAPI call to another agent"""
    try:
        if not target_agent:
            return "Please select a target agent first"
            
        auth_token = os.getenv('VAPI_AUTH_TOKEN')
        if not auth_token:
            return "Missing VAPI authentication token"
            
        target_agent_id = get_agent_id(target_agent)
        if not target_agent_id:
            return f"Agent ID not found for {target_agent}"
        
        vapi = Vapi(api_key=auth_token)
        result = vapi.forward_call(target_agent_id)
        
        return result
        
    except Exception as e:
        print(f"Error in forward_vapi_call: {str(e)}")
        return f"Error forwarding call: {str(e)}"

def start_vapi_call(agent, name, number, mailing_address, source_name=""):
    """Start a VAPI call with the given contact information dynamically."""
    try:
        if not all([agent, name, number, mailing_address]):
            return "Please provide all required information."

        # Dynamically detect agent ID
        agent_id = get_agent_id(agent)
        if not agent_id:
            return f"Agent ID not found for {agent}."
        
        # Fetch VAPI credentials from environment variables
        auth_token = os.getenv('VAPI_AUTH_TOKEN')
        vapi_phone_number_id = os.getenv('VAPI_PHONE_NUMBER_ID')
        if not auth_token or not vapi_phone_number_id:
            return "Missing VAPI credentials in environment variables."

        try:
            formatted_number = format_phone_number(number)
        except ValueError as e:
            return f"Invalid phone number: {str(e)}"

        # Construct the full conversation script
        conversation_script = {
            "initial_greeting": f"Hi, this is {agent} from CuriousKid. Am I speaking with {name}?",
            "registration_confirmation": f"I see you registered on our website through {source_name} and expressed interest in our Robotics and AI courses. Do you recall this registration?",
            "availability_check": "Thank you! I wanted to discuss supporting your child's STEM learning journey. Do you have a few minutes to talk?",
            "identity_recheck": f"Just to confirm, is this {name}?",
            "identity_confusion": f"Sorry for the confusion, just to double-check, is your name {name}?",
            "identity_confirmed": f"That's wonderful, {name}! I'll be happy to assist you in getting more details about our programs and setting up a session for your child.",
            "student_details": "Could you please tell me your child's name and their grade?",
            "age_confirmation": "Based on their grade, [Child's Name] would approximately be around [Calculated Age] years old. Is that correct?",
            "location_confirmation": f"May I confirm your current location? Is it {mailing_address}?",
            "technical_requirements": "Does [Child's Name] have access to a laptop and a stable internet connection for the sessions?",
            "parent_profession": "If I may ask, what is your profession?",
            "spouse_profession": "Could you also share what your spouse does professionally?",
            "motivation": "I believe you've seen our advertisement on emerging technologies like robotics and artificial intelligence. Could you share what motivated you to register [Child's Name]?",
            "company_overview": "That's fantastic to hear! CuriousKid is India's largest innovation training company, specializing in teaching kids advanced technologies like electronics, robotics, artificial intelligence, and entrepreneurship. Did you know that kids aged 8 to 16 years have achieved over 170 patents through our programs? It's truly inspiring!",
            "diagnostic_session": "To facilitate admissions, we conduct a diagnostic session where our STEM expert engages with your child for about 10-15 minutes to assess their interests and aptitude through simple experiments.",
            "scheduling": "I'd love to schedule this session today! What time works best for you?",
            "concerns_time": "I completely understand how busy schedules can be. If this is not the right time, we can set up a follow-up call at a more convenient time for you. Does that work?",
            "concerns_relevance": "I hear you! Many parents wonder if these courses will truly benefit their children. I'd be happy to share examples of how kids have excelled through our programs. For instance, some students as young as 10 have designed their own robots or secured patents! Would you like to know more about their success stories?",
            "closing": "Thank you for your time! If you have any questions or need further assistance, please don't hesitate to reach out. Have a great day!"
        }

        # Create dynamic context with the full script
        initial_context = {
            "customer_info": {
                "name": name,
                "mailing_address": mailing_address,
                "source": source_name
            },
            "conversation_script": conversation_script,
            "course_info": {
                "little_innovator": {
                    "grades": "1-2",
                    "modules": ["Little Innovator 1", "Little Innovator 2"],
                    "duration": "6 months per module",
                    "fee": "eighteen thousandx rupees per module"
                },
                "emerging_tech": {
                    "grades": "3 and above",
                    "modules": [
                        "Electronics",
                        "Embedded Design and Robotics",
                        "Internet of Things (IoT)",
                        "Artificial Intelligence",
                        "Entrepreneurship"
                    ],
                    "duration": "6 months per module",
                    "fee": "twenty thousand rupees per module"
                }
            }
        }

        call_payload = {
            'assistantId': agent_id,
            'phoneNumberId': vapi_phone_number_id,
            'customer': {
                'name': name,
                'number': formatted_number
            },
            'metadata': {
                'name': name,
                'mailing_address': mailing_address,
                'source': source_name
            },
            'assistantOverrides': {
                'variableValues': {
                    'name': name,
                    'mailing_address': mailing_address,
                    'source': source_name
                },
                'context': json.dumps(initial_context)
            }
        }
        
        print(f"Making call to {formatted_number}")
        print(f"Using agent ID: {agent_id}")
        print(f"Call payload: {json.dumps(call_payload, indent=2)}")

        response = requests.post(
            'https://api.vapi.ai/call/phone',
            headers={
                'Authorization': f'Bearer {auth_token}',
                'Content-Type': 'application/json'
            },
            json=call_payload
        )
        
        if response.status_code in [200, 201]:
            call_data = response.json()
            call_id = call_data.get('id')
            
            start_call_recording(call_id, agent_id, name, formatted_number)
            
            polling_thread = threading.Thread(
                target=poll_call_status,
                args=(call_id, agent_id, name, formatted_number, {
                    'Authorization': f'Bearer {auth_token}',
                    'Content-Type': 'application/json'
                })
            )
            polling_thread.daemon = True
            polling_thread.start()
            
            return f"Started call for {name} with phone number {formatted_number}."
        else:
            return f"Failed to start call: {response.text}"

    except Exception as e:
        return f"Error starting call: {str(e)}"


def process_csv_and_make_calls(file_path, selected_agent):
    """Process CSV file and make calls to each number"""
    try:
        if not file_path:
            return "Please upload a CSV file"
            
        df = pd.read_csv(file_path.name)
        results = []
        
        required_columns = ['contact_number', 'contact_name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return f"Missing required columns in CSV: {', '.join(missing_columns)}"
        
        for index, row in df.iterrows():
            try:
                contact_number = str(row['contact_number']).strip()
                contact_name = str(row['contact_name']).strip()
                
                if not contact_number.startswith('+'):
                    contact_number = '+' + contact_number
                
                result = start_vapi_call(selected_agent, contact_name, contact_number)
                
                results.append({
                    'number': contact_number,
                    'name': contact_name,
                    'status': 'success' if 'successfully' in result else 'failed',
                    'message': result
                })
                
                time.sleep(2) 
                
            except Exception as e:
                results.append({
                    'number': contact_number if 'contact_number' in locals() else 'Unknown',
                    'name': contact_name if 'contact_name' in locals() else 'Unknown',
                    'status': 'failed',
                    'message': str(e)
                })
        
        output = "CSV Processing Results:\n\n"
        for result in results:
            output += f"Name: {result['name']}\n"
            output += f"Number: {result['number']}\n"
            output += f"Status: {result['status']}\n"
            output += f"Message: {result['message']}\n"
            output += "-" * 50 + "\n"
        
        return output
    
    except Exception as e:
        error_msg = f"Error processing CSV: {str(e)}"
        print(error_msg)
        return error_msg

def get_agent_id(agent_name):
    """Get agent ID from environment variables based on agent name"""
    try:
        agent_env_map = {
            "unpod-English": "VAPI_AGENT_UNPOD_ENGLISH",
            "health-insurance": "AGENT_HEALTH_INSURANCE",
            "unpod-hindi": "AGENT_UNPOD_HINDI",
            "Quriouskid-English": "AGENT_QURIOUSKID_ENGLISH",
            "Quriouskid-script-hindi": "AGENT_QURIOUSKID_SCRIPT_HINDI",
            "Realestate-hindi": "AGENT_REALESTATE_HINDI",
            "Realestate-english": "AGENT_REALESTATE_ENGLISH"
        }
        
        env_var = agent_env_map.get(agent_name)
        if not env_var:
            raise ValueError(f"No environment variable mapping found for agent: {agent_name}")
            
        agent_id = os.getenv(env_var)
        if not agent_id:
            raise ValueError(f"Agent ID not found in environment variables for: {agent_name}")
            
        return agent_id
        
    except Exception as e:
        print(f"Error getting agent ID: {str(e)}")
        return None

def launch_gradio_interface():
    """Launch the Gradio interface for VAPI calls"""
    import gradio as gr
    
    # Create the interface
    with gr.Blocks() as demo:
        gr.Markdown("# VAPI Call Interface")
        
        with gr.Row():
            with gr.Column():
                agent_selector = gr.Dropdown(
                    choices=[
                        "unpod-English",
                        "health-insurance",
                        "unpod-hindi",
                        "Quriouskid-English",
                        "Quriouskid-script-hindi",
                        "Realestate-hindi",
                        "Realestate-english"
                    ],
                    label="Select Agent",
                    value="Quriouskid-English"
                )
                contact_name = gr.Textbox(label="Contact Name")
                contact_number = gr.Textbox(label="Contact Number")
                mailing_address = gr.Textbox(label="Mailing Address")
                source_name = gr.Textbox(
                    label="Source Name",
                    value="Instagram",
                    placeholder="Enter source (e.g. Instagram, Facebook)"
                )
                
        with gr.Row():
            start_button = gr.Button("Start Call")
            
        output_text = gr.Textbox(label="Output")

        def wrapped_start_vapi_call(agent, name, number, address, source):
            return start_vapi_call(agent, name, number, address, source)
        
        # Single call button logic
        start_button.click(
            fn=wrapped_start_vapi_call,
            inputs=[
                agent_selector,
                contact_name,
                contact_number,
                mailing_address,
                source_name
            ],
            outputs=output_text
        )
        
    # Launch the interface
    demo.launch()

class CallRecorder:
    def __init__(self, call_id, agent_id, customer_name, customer_number):
        self.call_id = call_id
        self.agent_id = agent_id
        self.customer_name = customer_name
        self.customer_number = customer_number
        self.pcm_buffer = bytearray()
        self.recording_path = None
        self.is_recording = True

    def save_recording_to_mongodb(self):
        """Save recording metadata and binary data to MongoDB"""
        try:
            db = get_mongodb_connection()
            if not db:
                return False

            audio_base64 = base64.b64encode(self.pcm_buffer).decode('utf-8')
            
            recording_doc = {
                'call_id': self.call_id,
                'agent_id': self.agent_id,
                'customer_name': self.customer_name,
                'customer_number': self.customer_number,
                'timestamp': datetime.now(),
                'audio_data': audio_base64,
                'audio_format': 'pcm',
                'file_path': self.recording_path
            }

            result = db.recordings.update_one(
                {'call_id': self.call_id},
                {'$set': recording_doc},
                upsert=True
            )
            print(f"Recording saved to MongoDB with ID: {result.upserted_id if result.upserted_id else self.call_id}")
            return True
        except Exception as e:
            print(f"Error saving recording to MongoDB: {str(e)}")
            return False

    def save_recording_to_file(self):
        """Save PCM buffer to file"""
        try:
            recordings_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recordings')
            os.makedirs(recordings_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{self.call_id}_{timestamp}.pcm"
            self.recording_path = os.path.join(recordings_dir, filename)
            
            with open(self.recording_path, 'wb') as f:
                f.write(self.pcm_buffer)
            print(f"Recording saved to: {self.recording_path}")
            return True
        except Exception as e:
            print(f"Error saving recording to file: {str(e)}")
            return False

    async def start_recording(self):
        """Start WebSocket connection and record audio"""
        ws_url = f"wss://aws-us-west-2-production1-phone-call-websocket.vapi.ai/{self.call_id}/transport"
        try:
            async with websockets.connect(ws_url) as websocket:
                print(f"WebSocket connection established for call {self.call_id}")
                
                while self.is_recording:
                    try:
                        message = await websocket.recv()
                        
                        if isinstance(message, bytes):
                            self.pcm_buffer.extend(message)
                            print(f"Received PCM data, buffer size: {len(self.pcm_buffer)}")
                        else:
                            print('Received message:', message)
                            
                    except websockets.exceptions.ConnectionClosed:
                        print("WebSocket connection closed")
                        break
                    except Exception as e:
                        print(f"Error receiving data: {str(e)}")
                        break
                
                if len(self.pcm_buffer) > 0:
                    self.save_recording_to_file()
                    self.save_recording_to_mongodb()
                    
        except Exception as e:
            print(f"WebSocket connection error: {str(e)}")

    def stop_recording(self):
        """Stop the recording"""
        self.is_recording = False

async def start_call_recording(call_id, agent_id, customer_name, customer_number):
    recorder = CallRecorder(call_id, agent_id, customer_name, customer_number)
    await recorder.start_recording()
    return recorder

def poll_call_status(call_id, agent_id, customer_name, customer_number, headers):
    start_time = int(time.time() * 1000)
    transcript = []
    last_message_count = 0
    transcript_extractor = TranscriptExtractor()
    
    recorder = None
    recording_task = None
    
    async def setup_recording():
        nonlocal recorder
        recorder = await start_call_recording(call_id, agent_id, customer_name, customer_number)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    recording_task = loop.create_task(setup_recording())
    
    while True:
        try:
            status_response = requests.get(
                f'https://api.vapi.ai/call/{call_id}',
                headers=headers
            )
            
            if status_response.status_code == 200:
                call_data = status_response.json()
                current_status = call_data.get('status')
                print(f"Call Status: {current_status}")
                
                messages_response = requests.get(
                    f'https://api.vapi.ai/call/{call_id}/messages',
                    headers=headers
                )
                
                if messages_response.status_code == 200:
                    messages = messages_response.json()
                    
                    if len(messages) > last_message_count:
                        for msg in messages[last_message_count:]:
                            formatted_msg = {
                                "role": "bot" if msg.get('role') == 'assistant' else "user",
                                "time": int(msg.get('timestamp', start_time)),
                                "source": msg.get('source', ''),
                                "endTime": int(msg.get('timestamp', start_time)) + (msg.get('duration', 0) * 1000),
                                "message": msg.get('text', ''),
                                "duration": float(msg.get('duration', 0)) * 1000,
                                "secondsFromStart": (int(msg.get('timestamp', start_time)) - start_time) / 1000
                            }
                            transcript.append(formatted_msg)
                            print(f"New message: {formatted_msg}")
                        
                        last_message_count = len(messages)
                        
                        save_transcript_to_mongodb(call_id, agent_id, customer_name, customer_number, transcript)
                        
                        extracted_messages = transcript_extractor.extract_messages(transcript)
                        txt_path = transcript_extractor.generate_readable_transcript(extracted_messages, call_id, "txt")
                        json_path = transcript_extractor.generate_readable_transcript(extracted_messages, call_id, "json")
                        print(f"Generated transcript files: \nTXT: {txt_path}\nJSON: {json_path}")
                
                if current_status in ['completed', 'failed']:
                    if recorder:
                        recorder.stop_recording()
                    if recording_task:
                        loop.run_until_complete(recording_task)
                    loop.close()
                    
                    print(f"Call {current_status}. Final transcript and recording saved.")
                    break
                    
            time.sleep(2)
            
        except Exception as e:
            print(f"Error polling call status: {str(e)}")
            time.sleep(2)
            
        finally:
            if current_status in ['completed', 'failed']:
                if recorder:
                    recorder.stop_recording()
                if recording_task:
                    loop.run_until_complete(recording_task)
                loop.close()

class TranscriptExtractor:
    def __init__(self):
        self.transcript_dir = os.path.dirname(os.path.abspath(__file__))

    def extract_messages(self, transcript_json):
        messages = []
        try:
            if isinstance(transcript_json, str):
                transcript_data = json.loads(transcript_json)
            else:
                transcript_data = transcript_json

            for message in transcript_data:
                role = "assistant" if message.get("role") == "bot" else "user"
                content = message.get("message", "")
                timestamp = message.get("time", "")
                
                if content:
                    messages.append({
                        "role": role,
                        "content": content,
                        "timestamp": timestamp
                    })
        except Exception as e:
            print(f"Error extracting messages: {str(e)}")
        
        return messages

    def generate_readable_transcript(self, messages, call_id, output_format="txt"):
        if not messages:
            return "No messages found in transcript"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_format == "txt":
            output = f"Conversation Transcript (Generated at {timestamp})\n"
            output += f"Call ID: {call_id}\n"
            output += "=" * 50 + "\n\n"
            
            for msg in messages:
                role = msg["role"].capitalize()
                content = msg["content"]
                msg_time = datetime.fromtimestamp(msg["timestamp"]/1000).strftime("%Y-%m-%d %H:%M:%S")
                
                output += f"{role}: {content}\n"
                output += f"Time: {msg_time}\n"
                output += "-" * 30 + "\n"
            
            filename = f"transcript_{call_id}.txt"
            filepath = os.path.join(self.transcript_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(output)
            
            return filepath
        
        elif output_format == "json":
            output = {
                "call_id": call_id,
                "generated_at": timestamp,
                "messages": messages
            }
            
            filename = f"transcript_{call_id}.json"
            filepath = os.path.join(self.transcript_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            return filepath

def save_transcript_to_file(call_id, transcript):
    try:
        filename = f'transcript_{call_id}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(transcript, f, ensure_ascii=False, indent=2)
        print(f"Transcript saved to file: {filename}")
    except Exception as e:
        print(f"Error saving transcript to file: {str(e)}")

def read_contacts_from_csv(file_path):
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
            
        contacts = pd.read_csv(file_path)
        print(f"Available columns in CSV: {contacts.columns.tolist()}")
        
        mobile_columns = ['Mobile Number', 'Mobile', 'Phone Number', 'Phone', 'Contact Number', 'Number']
        name_columns = ['Contact Name', 'Name', 'Full Name', 'Contact']
        
        mobile_col = next((col for col in mobile_columns if col in contacts.columns), None)
        name_col = next((col for col in name_columns if col in contacts.columns), None)
        
        missing_columns = []
        if not mobile_col:
            missing_columns.append(f"Mobile Number (accepted: {', '.join(mobile_columns)})")
        if not name_col:
            missing_columns.append(f"Contact Name (accepted: {', '.join(name_columns)})")
            
        if missing_columns:
            raise ValueError(f"Missing required columns in CSV: {missing_columns}")
        
        contacts = contacts.rename(columns={
            mobile_col: 'Mobile Number',
            name_col: 'Contact Name'
        })
        
        contacts['Mobile Number'] = contacts['Mobile Number'].astype(str).apply(
            lambda x: f"+91{x.strip()}" if not str(x).strip().startswith("+91") else x.strip()
        )
        
        return contacts[['Mobile Number', 'Contact Name']].to_dict(orient='records')
        
    except pd.errors.EmptyDataError:
        raise ValueError("The CSV file is empty")
    except Exception as e:
        raise Exception(f"Error reading CSV file: {str(e)}")

def format_phone_number(phone):
    phone = ''.join(filter(lambda x: x.isdigit() or x == '+', str(phone)))
    phone = phone.lstrip('+').lstrip('91')
    
    if len(phone) > 10:
        phone = phone[-10:]
    elif len(phone) < 10:
        raise ValueError("Phone number must be at least 10 digits")
    
    return f"+91{phone}"

def get_agent_prompt(agent_id, auth_token):
    """Fetch the agent's prompt from VAPI API"""
    try:
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        
        url = f'https://api.vapi.ai/assistant/{agent_id}'
        print(f"Fetching agent prompt from: {url}")
        
        response = requests.get(url, headers=headers)
        print(f"Agent prompt response status: {response.status_code}")
        print(f"Agent prompt response: {response.text}")
        
        if response.status_code == 200:
            agent_data = response.json()
            prompt = agent_data.get('prompt', '')
            if prompt:
                print(f"Successfully fetched agent prompt")
                return prompt
            else:
                print("No prompt found in agent data")
                return None
        else:
            print(f"Failed to fetch agent prompt: {response.text}")
            # Continue without prompt instead of failing
            return ""
            
    except Exception as e:
        print(f"Error fetching agent prompt: {str(e)}")
        # Continue without prompt instead of failing
        return ""

def get_course_presentation(grade, child_name):
    """Generate a detailed course presentation based on grade"""
    if 1 <= grade <= 2:
        course_type = "little_innovator"
        presentation = (
            f"Based on {child_name}'s grade, let me tell you about our Little Innovator Program.\n\n"
            "This is our entry-level course specially designed for grades 1-2. "
            "The program consists of two modules, each lasting six months.\n\n"
            "In this program, your child will learn:\n"
            "1. Basic coding concepts through interactive sessions\n"
            "2. Hands-on robotics projects\n"
            "3. Creative electronics activities\n\n"
            "Classes are held twice a week in small groups of up to 10 students. "
            "Our instructors are alumni from prestigious institutions with experience in teaching young learners.\n\n"
            "The program fee is eighteen thousand rupees per module.\n\n"
            "(Pause for questions)\n\n"
            f"Would you like to know how {child_name} can specifically benefit from this program?"
        )
    else:
        course_type = "emerging_tech"
        presentation = (
            f"For {child_name}, I recommend our comprehensive Emerging Tech Course, "
            "which is perfect for grade 3 and above.\n\n"
            "This advanced program consists of five specialized modules:\n"
            "1. Electronics: Understanding circuits and components\n"
            "2. Embedded Design and Robotics: Building robots with sensors\n"
            "3. Internet of Things (IoT): Learning device connectivity\n"
            "4. Artificial Intelligence: Basics of AI and machine learning\n"
            "5. Entrepreneurship: Innovation and business skills\n\n"
            "Each module lasts 6 months with classes twice a week. "
            "Our instructors are graduates from top engineering colleges with expertise in their fields.\n\n"
            "The program fee is twenty-four thousand rupees per module.\n\n"
            "(Pause for questions)\n\n"
            f"Would you like to know how this program can prepare {child_name} for future technologies?"
        )
    
    return {
        "course_type": course_type,
        "presentation": presentation,
        "next_step": "Would you like to schedule a diagnostic session to assess your child's interests and aptitude?"
    }

if __name__ == "__main__":
    launch_gradio_interface()