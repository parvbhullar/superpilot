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
from transcript_extractor import format_phone_number

class CallSummary:
    def __init__(self):
        self.summary_data = {
            'customer_name': None,
            'child_name': None,
            'child_grade': None,
            'call_duration': None,
            'call_outcome': None,
            'key_points': [],
            'action_items': [],
            'next_steps': []
        }
        self.call_start = datetime.now().isoformat()  # Capture the call start time

    def update_summary(self, key, value):
        if key in self.summary_data:
            self.summary_data[key] = value

    def save_summary_to_file(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"summary_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(self.summary_data, f, indent=4)
            
            print(f"\nSaved call summary to {filename}")
            return filename
        except Exception as e:
            print(f"Error saving summary: {str(e)}")
            return None

    def generate_summary(self):
        summary = "\n=== CALL SUMMARY ===\n"
        summary += f"Call Duration: {self._calculate_duration()}\n"
        summary += f"Customer Name: {self.summary_data['customer_name'] or 'Not captured'}\n"
        summary += f"Child's Name: {self.summary_data['child_name'] or 'Not captured'}\n"
        summary += f"Child's Grade: {self.summary_data['child_grade'] or 'Not captured'}\n"
        
        if self.summary_data.get('course_discussed'):
            summary += f"Course Discussed: {self.summary_data['course_discussed']}\n"
        
        summary += "Key Points:\n" + "\n".join(self.summary_data['key_points']) + "\n"
        summary += "Action Items:\n" + "\n".join(self.summary_data['action_items']) + "\n"
        summary += "Next Steps:\n" + "\n".join(self.summary_data['next_steps']) + "\n"
        summary += "====================\n"
        return summary

    def save_mom(mom_summary):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mom_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write(mom_summary)
            
            print(f"\nSaved MoM to {filename}")
        except Exception as e:
            print(f"Error saving MoM: {str(e)}")


# Load environment variables
load_dotenv()
conversation_flow = {
    'student_details': {
        'gather_info': {
            'callback': None
        }
    }
}
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
        
    def __init__(self, api_key=None, mongo_client=None):
        if not hasattr(self, 'initialized'):
            self.api_key = api_key
            self.mongo_client = mongo_client
            self.db = mongo_client['vapi-script'] if mongo_client else None
            self.mom_generator = MOMGenerator()
            self.current_call_id = None
            self.agent_id = None
            self.contact_name = None
            self.call_start_time = None
            self.mom = None
            self.call_summary = CallSummary()
            self.openai_api_key = None
            self._client = None
            self.transcript_processor = None


            
            self.conversation_vocabulary = {
                'greetings': {
                    'hello': 'नमस्ते',
                    'welcome': 'स्वागत है',
                    'thank you': 'धन्यवाद',
                    'thanks': 'धन्यवाद',
                    'great': 'भुत अच्छा',
                    'discuss': 'चर्चा'
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

    def process_call_data(self, transcript):
        """Main processing pipeline with MoM generation"""
        try:
            # Generate MoM
            call_metadata = {
                'call_id': self.current_call_id,
                'agent_id': self.agent_id,
                'customer_name': self.contact_name,
                'start_time': self.call_start_time.isoformat() if self.call_start_time else 'N/A'
            }
            
            self.mom = self.mom_generator.generate_mom(transcript, call_metadata)
            
            if self.mom:
                self.save_mom_to_file()
                self.save_mom_to_mongodb()
            
            return self.mom
        except Exception as e:
            print(f"Error processing call data: {str(e)}")
            return None

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
                self.call_summary.update_summary('budget_mentioned', self.user_budget)  # Update call summary with budget
                
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
                self.call_summary.update_summary('location_confirmed', self.user_location)  # Update call summary with location
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
                self.call_summary.update_summary('profession_info', self.user_profession)  # Update call summary with profession
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

        # Add summary updates
        if "grade" in translated_message.lower():
            self.call_summary.update_summary('child_grade', self.user_grade)
        if "diagnostic session" in translated_message.lower():
            self.call_summary.update_summary('diagnostic_scheduled', True)

        print(f"Processing user message: {message}")

        # If necessary, generate and print call summary at the end of the call
        if self.verification_stage == 3:
            print("Call Summary:", self.call_summary.generate_summary())

    class TranscriptProcessor:
        def __init__(self, transcript_data):
            self.transcript_data = transcript_data
            self.summary = {
                'student_name': None,
                'grade': None,
                'call_outcome': None,
                'interests': [],
                'key_points': [],
                'action_items': []
            }

        def extract_key_info(self):
            try:
                messages = self.transcript_data.get('messages', [])
                for message in messages:
                    text = message.get('text', '').lower()
                    role = message.get('role', '')
                    # Extract student name from user's message
                    if 'name is' in text and role == 'user':
                        name_match = re.search(r'name is (\w+)', text, re.I)
                        if name_match:
                            self.summary['student_name'] = name_match.group(1)
                    # Extract grade
                    if 'grade' in text:
                        grade_match = re.search(r'grade (\d+)', text)
                        if grade_match:
                            self.summary['grade'] = grade_match.group(1)
                    # Extract interests
                    if any(word in text for word in ['interested', 'like', 'want', 'prefer']):
                        self.summary['interests'].append(text)
                    # Extract key points from agent messages
                    if role == 'assistant' and len(text) > 30:
                        self.summary['key_points'].append(text)
                    # Extract action items
                    if any(word in text for word in ['will', 'shall', 'need to', 'must']):
                        self.summary['action_items'].append(text)
                # Remove duplicates
                self.summary['interests'] = list(set(self.summary['interests']))
                self.summary['key_points'] = list(set(self.summary['key_points']))
                self.summary['action_items'] = list(set(self.summary['action_items']))
                return self.summary
            except Exception as e:
                print(f"Error extracting key info: {str(e)}")
                return self.summary
    
    def generate_call_analysis(transcript_data):
        """Generate call analysis with outcome extracted from transcript"""
        messages = transcript_data.get('messages', [])
        
        # Initialize outcome detection
        indicators = {
            'SCHEDULED': 0,
            'FOLLOW_UP': 0,
            'NOT_INTERESTED': 0
        }
        
        for msg in messages:
            text = msg.get('text', '').lower()
            role = msg.get('role', '')
            
            # Check for scheduling indicators
            if any(word in text for word in ['schedule', 'book', 'confirm', 'appointment']):
                indicators['SCHEDULED'] += 2
            
            # Check for follow-up indicators
            if any(word in text for word in ['call back', 'follow up', 'think about', 'later']):
                indicators['FOLLOW_UP'] += 1
                
            # Check for not interested indicators
            if any(word in text for word in ['not interested', 'no thanks', 'too expensive']):
                indicators['NOT_INTERESTED'] += 2
        
        # Determine outcome based on indicators
        max_indicator = max(indicators.items(), key=lambda x: x[1])
        detected_outcome = max_indicator[0] if max_indicator[1] > 0 else 'UNKNOWN'
        
        # Process transcript for other information
        processor = TranscriptProcessor(transcript_data)
        key_info = processor.extract_key_info()
        
        analysis = {
            "summary": f"Call outcome: {detected_outcome}",
            "structuredData": {
                **key_info,
                "callOutcome": detected_outcome,
                "indicators": indicators
            },
            "successEvaluation": "Success" if detected_outcome == 'SCHEDULED' else "Needs follow-up"
        }
        
        return analysis

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
                self.call_summary.update_summary('budget_mentioned', self.user_budget)  # Update call summary with budget
                
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
                self.call_summary.update_summary('location_confirmed', self.user_location)  # Update call summary with location
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
                self.call_summary.update_summary('profession_info', self.user_profession)  # Update call summary with profession
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

        # Add summary updates
        if "grade" in translated_message.lower():
            self.call_summary.update_summary('child_grade', self.user_grade)
        if "diagnostic session" in translated_message.lower():
            self.call_summary.update_summary('diagnostic_scheduled', True)

        print(f"Processing user message: {message}")

        # If necessary, generate and print call summary at the end of the call
        if self.verification_stage == 3:
            print("Call Summary:", self.call_summary.generate_summary())

    class TranscriptProcessor:
        def __init__(self, transcript_data):
            self.transcript_data = transcript_data
            self.summary = {
                'student_name': None,
                'grade': None,
                'interests': [],
                'key_points': [],
                'action_items': []
            }

        def extract_key_info(self):
            try:
                messages = self.transcript_data.get('messages', [])
                for message in messages:
                    text = message.get('text', '').lower()
                    role = message.get('role', '')
                    # Extract student name from user's message
                    if 'name is' in text and role == 'user':
                        name_match = re.search(r'name is (\w+)', text, re.I)
                        if name_match:
                            self.summary['student_name'] = name_match.group(1)
                    # Extract grade
                    if 'grade' in text:
                        grade_match = re.search(r'grade (\d+)', text)
                        if grade_match:
                            self.summary['grade'] = grade_match.group(1)
                    # Extract interests
                    if any(word in text for word in ['interested', 'like', 'want', 'prefer']):
                        self.summary['interests'].append(text)
                    # Extract key points from agent messages
                    if role == 'assistant' and len(text) > 30:
                        self.summary['key_points'].append(text)
                    # Extract action items
                    if any(word in text for word in ['will', 'shall', 'need to', 'must']):
                        self.summary['action_items'].append(text)
                # Remove duplicates
                self.summary['interests'] = list(set(self.summary['interests']))
                self.summary['key_points'] = list(set(self.summary['key_points']))
                self.summary['action_items'] = list(set(self.summary['action_items']))
                return self.summary
            except Exception as e:
                print(f"Error extracting key info: {str(e)}")
                return self.summary
    
    def generate_call_analysis(transcript_data, call_outcome):
        """
        Generate a call analysis JSON object.
        
        Parameters:
        - transcript_data: Dictionary with transcript data (should contain a 'messages' key).
        - call_outcome: Outcome of the call (e.g., "completed", "failed").
        
        Returns:
        A dictionary with keys "summary", "structuredData", and "successEvaluation".
        """
        # Extract key details using TranscriptProcessor
        processor = TranscriptProcessor(transcript_data)
        key_info = processor.extract_key_info()
        
        # Build a narrative summary from the extracted info
        summary_lines = []
        if key_info.get('student_name'):
            summary_lines.append(f"Student Name: {key_info['student_name']}.")
        else:
            summary_lines.append("Student name not provided.")
        if key_info.get('grade'):
            summary_lines.append(f"Grade: {key_info['grade']}.")
        else:
            summary_lines.append("Grade not provided.")
        if key_info.get('key_points'):
            summary_lines.append("Key points: " + "; ".join(key_info['key_points']) + ".")
        if key_info.get('action_items'):
            summary_lines.append("Action items: " + "; ".join(key_info['action_items']) + ".")
        narrative_summary = " ".join(summary_lines)
        
        # Evaluate call success based on outcome
        if call_outcome.lower() == "completed":
            success_eval = "The call was successful. The customer engaged well and necessary information was gathered."
        else:
            success_eval = "The call was not fully successful. Follow-up is required for missing details or concerns."
        
        analysis = {
            "summary": narrative_summary,
            "structuredData": key_info,
            "successEvaluation": success_eval
        }
        return analysis

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
                self.call_summary.update_summary('budget_mentioned', self.user_budget)  # Update call summary with budget
                
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
                self.call_summary.update_summary('location_confirmed', self.user_location)  # Update call summary with location
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
                self.call_summary.update_summary('profession_info', self.user_profession)  # Update call summary with profession
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

        # Add summary updates
        if "grade" in translated_message.lower():
            self.call_summary.update_summary('child_grade', self.user_grade)
        if "diagnostic session" in translated_message.lower():
            self.call_summary.update_summary('diagnostic_scheduled', True)

        print(f"Processing user message: {message}")

        # If necessary, generate and print call summary at the end of the call
        if self.verification_stage == 3:
            print("Call Summary:", self.call_summary.generate_summary())

    class TranscriptProcessor:
        def __init__(self, transcript_data):
            self.transcript_data = transcript_data
            self.summary = {
                'student_name': None,
                'grade': None,
                'interests': [],
                'key_points': [],
                'action_items': []
            }

        def extract_key_info(self):
            try:
                messages = self.transcript_data.get('messages', [])
                for message in messages:
                    text = message.get('text', '').lower()
                    role = message.get('role', '')
                    # Extract student name from user's message
                    if 'name is' in text and role == 'user':
                        name_match = re.search(r'name is (\w+)', text, re.I)
                        if name_match:
                            self.summary['student_name'] = name_match.group(1)
                    # Extract grade
                    if 'grade' in text:
                        grade_match = re.search(r'grade (\d+)', text)
                        if grade_match:
                            self.summary['grade'] = grade_match.group(1)
                    # Extract interests
                    if any(word in text for word in ['interested', 'like', 'want', 'prefer']):
                        self.summary['interests'].append(text)
                    # Extract key points from agent messages
                    if role == 'assistant' and len(text) > 30:
                        self.summary['key_points'].append(text)
                    # Extract action items
                    if any(word in text for word in ['will', 'shall', 'need to', 'must']):
                        self.summary['action_items'].append(text)
                # Remove duplicates
                self.summary['interests'] = list(set(self.summary['interests']))
                self.summary['key_points'] = list(set(self.summary['key_points']))
                self.summary['action_items'] = list(set(self.summary['action_items']))
                return self.summary
            except Exception as e:
                print(f"Error extracting key info: {str(e)}")
                return self.summary
    
    def generate_call_analysis(transcript_data, call_outcome):
        """
        Generate a call analysis JSON object.
        
        Parameters:
        - transcript_data: Dictionary with transcript data (should contain a 'messages' key).
        - call_outcome: Outcome of the call (e.g., "completed", "failed").
        
        Returns:
        A dictionary with keys "summary", "structuredData", and "successEvaluation".
        """
        # Extract key details using TranscriptProcessor
        processor = TranscriptProcessor(transcript_data)
        key_info = processor.extract_key_info()
        
        # Build a narrative summary from the extracted info
        summary_lines = []
        if key_info.get('student_name'):
            summary_lines.append(f"Student Name: {key_info['student_name']}.")
        else:
            summary_lines.append("Student name not provided.")
        if key_info.get('grade'):
            summary_lines.append(f"Grade: {key_info['grade']}.")
        else:
            summary_lines.append("Grade not provided.")
        if key_info.get('key_points'):
            summary_lines.append("Key points: " + "; ".join(key_info['key_points']) + ".")
        if key_info.get('action_items'):
            summary_lines.append("Action items: " + "; ".join(key_info['action_items']) + ".")
        narrative_summary = " ".join(summary_lines)
        
        # Evaluate call success based on outcome
        if call_outcome.lower() == "completed":
            success_eval = "The call was successful. The customer engaged well and necessary information was gathered."
        else:
            success_eval = "The call was not fully successful. Follow-up is required for missing details or concerns."
        
        analysis = {
            "summary": narrative_summary,
            "structuredData": key_info,
            "successEvaluation": success_eval
        }
        return analysis

    def save_mom_to_file(self):
        """Save MOM to a specified file"""
        try:
            if not self.mom:
                print("No MoM to save.")
                return False

            # Use the provided local time as the source of truth for timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            call_id = self.current_call_id or f"call_{timestamp}"
            
            # Save text version directly to the specified path
            txt_filename = "/home/dev2/projects/super-pilot/super-pilot/work/superpilot/superpilot/superpilot/examples/channels/vapi-calls/test_file.txt"
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(self.mom['text_version'])
            
            # Save structured version
            json_filename = f"mom_{call_id}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(self.mom['structured_version'], f, indent=4)
            
            print(f"MOM saved to files: {txt_filename}, {json_filename}")
            return True
        except Exception as e:
            print(f"Error saving MOM to file: {str(e)}")
            return False

    def save_mom_to_mongodb(self):
        """Save MoM to MongoDB"""
        try:
            db = get_mongodb_connection()
            if not db:
                return False

            # Create MoM document
            mom_doc = {
                'call_id': self.current_call_id,
                'agent_id': self.agent_id,
                'customer_name': self.contact_name,
                'timestamp': datetime.now(),
                'mom': self.mom,
                'status': 'completed'
            }

            # Update or insert into MongoDB
            result = db.moms.update_one(
                {'call_id': self.current_call_id},
                {'$set': mom_doc},
                upsert=True
            )
            print(f"MoM saved to MongoDB with ID: {result.upserted_id if result.upserted_id else self.current_call_id}")
            return True
        except Exception as e:
            print(f"Error saving MoM to MongoDB: {str(e)}")
            return False

    def save_contact_number(self, contact_number):
        """Save the contact number to MongoDB."""
        if contact_number:
            contact_doc = {
                'contact_number': contact_number,
                'timestamp': datetime.now()
            }
            try:
                Vapi._instance.contacts_collection.insert_one(contact_doc) 
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

    def save_transcript_to_mongodb(self, call_id, agent_id, customer_name, customer_number, transcript_data):
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

def generate_mom_from_transcript(transcript_text, call_id, agent_name, customer_name):
    """
    Generate Minutes of Meeting (MoM) from a call transcript.

    Parameters:
    - transcript_text: The text content of the call transcript.
    - call_id: Unique call identifier.
    - agent_name: Name of the agent handling the call.
    - customer_name: Name of the customer.

    Returns:
    - A dictionary containing structured MoM.
    """
    # Extract key details from the conversation
    student_name_match = re.search(r"child's name is (\w+)", transcript_text, re.I)
    student_grade_match = re.search(r"grade (\d+)", transcript_text, re.I)
    scheduling_match = re.search(r"schedule.*(morning|evening|afternoon)", transcript_text, re.I)

    student_name = student_name_match.group(1) if student_name_match else "Unknown"
    student_grade = student_grade_match.group(1) if student_grade_match else "Unknown"
    session_time = scheduling_match.group(1) if scheduling_match else "Not scheduled"

    # Extract key discussion points
    key_discussion_points = []
    if "robotics" in transcript_text.lower():
        key_discussion_points.append("Interest in Robotics course")
    if "ai" in transcript_text.lower() or "artificial intelligence" in transcript_text.lower():
        key_discussion_points.append("Interest in AI course")
    if "fees" in transcript_text.lower():
        key_discussion_points.append("Fee structure was discussed")

    # Identify next steps
    next_steps = []
    if session_time != "Not scheduled":
        next_steps.append(f"Session scheduled for {session_time}")
    else:
        next_steps.append("Follow-up required for scheduling")

    # Structure the MoM
    mom_data = {
        "call_id": call_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "participants": {
            "agent": agent_name,
            "customer": customer_name,
            "student": student_name
        },
        "student_grade": student_grade,
        "key_discussion_points": key_discussion_points,
        "next_steps": next_steps,
        "follow_up_required": session_time == "Not scheduled"
    }

    return mom_data

def save_contact_number(contact_number):
        """Save the contact number to MongoDB."""
        if contact_number:
            contact_doc = {
                'contact_number': contact_number,
                'timestamp': datetime.now()
            }
            try:
                Vapi._instance.contacts_collection.insert_one(contact_doc) 
                return "Contact number saved successfully."
            except Exception as e:
                return f"Error saving contact number: {e}"
        return "No contact number provided."


def extract_messages(transcript_json):
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

def generate_readable_transcript(messages, output_format="txt"):
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

def start_vapi_call(agent, name, number, mailing_address, source_name=""):
    """Start a dynamic VAPI call with MOM generation."""
    try:
        # Basic validation
        if not all([agent, name, number, mailing_address]):
            return "Please provide all required information."

        # Get current timestamp
        current_timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        formatted_number = format_phone_number(number)
        if not formatted_number:
            return "Invalid phone number format."

        agent_id = get_agent_id(agent)
        if not agent_id:
            return f"Agent {agent} not found."

        # Ensure location is defined
        location = mailing_address.split(',')[1].strip() if ',' in mailing_address else 'Unknown Location'

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
                "english": "To facilitate your child's learning, we offer a FREE diagnostic session where we'll assess their strengths and areas for improvement. The session will last about 45 minutes, and we'll provide personalized guidance.",
                "hindi": """
                Dekho, aapke bachche ki learning ko better banane ke liye, hum ek FREE diagnostic session offer kar rahe hain. Isme hum unki strengths aur improvement areas check karenge. Session sirf 45 minute ka hoga, and we'll give personalized guidance.
                """
            },
            "schedule_session": {
                "english": "I'd love to schedule this session today! What time works best for you? We have slots available in the morning between 10 AM to 12 PM, and evening between 4 PM to 7 PM.",
                "hindi": """
                Oh great! Chaliye aaj hi session schedule kar lete hain. Aapko kaunsa time suit karega? 
                """
            },
            "schedule_confirmation": {
                "english": "Perfect! I'll schedule the diagnostic session for [time]. Our STEM expert will call you at this time. Please ensure your child is available with a device (laptop/tablet) for this interactive session.",
                "hindi": """
                Perfect! Mai diagnostic session [time] ke liye schedule kar deti hu. Humare STEM expert aapko isi time call karenge. Bass ye ensure kar lijiye ki aapka bachcha ek device (laptop/tablet) ke saath ready ho, kyunki session interactive hoga.
                """
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

            # Prepare and print call summary
            call_summary = {
                "Agent": agent,
                "Customer Name": name,
                "Phone Number": formatted_number,
                "Mailing Address": mailing_address,
                "Location": location,
                "Timestamp": current_timestamp
            }

            print("Call Summary:")
            for key, value in call_summary.items():
                print(f"{key}: {value}")

            # Extract MoM and transcript (Placeholder implementation)
            mom_summary = "This is a placeholder for the minutes of meeting."  # Replace with actual MoM extraction logic
            transcript_data = extract_transcript(call_data)  # Implement this function based on your logic

            # Save MoM and transcript to files in current working directory
            save_mom(mom_summary, transcript_data)

            return f"Started call for {name} with phone number {formatted_number}."
        else:
            return f"Failed to start call: {response.text}"

    except Exception as e:
        return f"Error starting call: {str(e)}"

def generate_mom_from_transcript(transcript_text, call_id, agent_name, customer_name):
    """
    Generate Minutes of Meeting (MoM) from a call transcript.

    Parameters:
    - transcript_text: The text content of the call transcript.
    - call_id: Unique call identifier.
    - agent_name: Name of the agent handling the call.
    - customer_name: Name of the customer.

    Returns:
    - A dictionary containing structured MoM.
    """
    # Extract key details from the conversation
    student_name_match = re.search(r"child's name is (\w+)", transcript_text, re.I)
    student_grade_match = re.search(r"grade (\d+)", transcript_text, re.I)
    scheduling_match = re.search(r"schedule.*(morning|evening|afternoon)", transcript_text, re.I)

    student_name = student_name_match.group(1) if student_name_match else "Unknown"
    student_grade = student_grade_match.group(1) if student_grade_match else "Unknown"
    session_time = scheduling_match.group(1) if scheduling_match else "Not scheduled"

    # Extract key discussion points
    key_discussion_points = []
    if "robotics" in transcript_text.lower():
        key_discussion_points.append("Interest in Robotics course")
    if "ai" in transcript_text.lower() or "artificial intelligence" in transcript_text.lower():
        key_discussion_points.append("Interest in AI course")
    if "fees" in transcript_text.lower():
        key_discussion_points.append("Fee structure was discussed")

    # Identify next steps
    next_steps = []
    if session_time != "Not scheduled":
        next_steps.append(f"Session scheduled for {session_time}")
    else:
        next_steps.append("Follow-up required for scheduling")

    # Structure the MoM
    mom_data = {
        "call_id": call_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "participants": {
            "agent": agent_name,
            "customer": customer_name,
            "student": student_name
        },
        "student_grade": student_grade,
        "key_discussion_points": key_discussion_points,
        "next_steps": next_steps,
        "follow_up_required": session_time == "Not scheduled"
    }

    return mom_data

def save_contact_number(contact_number):
        """Save the contact number to MongoDB."""
        if contact_number:
            contact_doc = {
                'contact_number': contact_number,
                'timestamp': datetime.now()
            }
            try:
                Vapi._instance.contacts_collection.insert_one(contact_doc) 
                return "Contact number saved successfully."
            except Exception as e:
                return f"Error saving contact number: {e}"
        return "No contact number provided."


def extract_messages(transcript_json):
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

def generate_readable_transcript(messages, output_format="txt"):
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

def start_vapi_call(agent, name, number, mailing_address, source_name=""):
    """Start a VAPI call with the given contact information dynamically, record transcript and extract summary."""
    try:
        # Previous validation checks remain the same
        if not all([agent, name, number, mailing_address]):
            return "Please provide all required information."

        agent_id = get_agent_id(agent)
        if not agent_id:
            return f"Agent ID not found for {agent}."
        
        auth_token = os.getenv('VAPI_AUTH_TOKEN')
        vapi_phone_number_id = os.getenv('VAPI_PHONE_NUMBER_ID')
        if not auth_token or not vapi_phone_number_id:
            return "Missing VAPI credentials in environment variables."

        try:
            formatted_number = format_phone_number(number)
        except ValueError as e:
            return f"Invalid phone number format."

        # Ensure location is defined
        location = mailing_address.split(',')[1].strip() if ',' in mailing_address else 'Unknown Location'

        # Define the conversation flow with dynamic prompts, including course details
        conversation_flow = {
            "introduction_phase": {
                "greeting": {
                    "initial": f"Before we proceed, am I speaking with {name}?",
                    "wait_for_confirmation": True,
                    "introduction": f"Thank you! I'm Stem expert from CuriousKid. I see you registered on our website through Instagram and expressed interest in our Robotics and AI courses. Do you remember the registration? I wanted to talk to you about supporting your child's STEM learning journey. Do you have a little time?",
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
                "english": "To facilitate your child's learning, we offer a FREE diagnostic session where we'll assess their strengths and areas for improvement. The session will last about 45 minutes, and we'll provide personalized guidance.",
                "hindi": """
                Dekho, aapke bachche ki learning ko better banane ke liye, hum ek FREE diagnostic session offer kar rahe hain. Isme hum unki strengths aur improvement areas check karenge. Session sirf 45 minute ka hoga, and we'll give personalized guidance.
                """
            },
            "schedule_session": {
                "english": "I'd love to schedule this session today! What time works best for you? We have slots available in the morning between 10 AM to 12 PM, and evening between 4 PM to 7 PM.",
                "hindi": """
                Oh great! Chaliye aaj hi session schedule kar lete hain. Aapko kaunsa time suit karega? 
                """
            },
            "schedule_confirmation": {
                "english": "Perfect! I'll schedule the diagnostic session for [time]. Our STEM expert will call you at this time. Please ensure your child is available with a device (laptop/tablet) for this interactive session.",
                "hindi": """
                Perfect! Mai diagnostic session [time] ke liye schedule kar deti hu. Humare STEM expert aapko isi time call karenge. Bass ye ensure kar lijiye ki aapka bachcha ek device (laptop/tablet) ke saath ready ho, kyunki session interactive hoga.
                """
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
            "conversation_script": conversation_flow,
            "course_info": {
                "little_innovator": {
                    "grades": "1-2",
                    "modules": ["Little Innovator 1", "Little Innovator 2"],
                    "duration": "6 months per module",
                    "fee": "eighteen thousand rupees per module"
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
                    "fee": "twenty four thousand rupees per module"
                }
            },
            "summary_schema": {
                "structuredDataSchema": {
                    "type": "object",
                    "properties": {
                        "studentName": {"type": "string"},
                        "studentGrade": {"type": "string"},
                        "parentName": {"type": "string"},
                        "selectedProgram": {"type": "string"},
                        "sessionScheduled": {"type": "boolean"},
                        "scheduledDateTime": {"type": "string"},
                        "parentProfession": {"type": "string"},
                        "technicalRequirements": {
                            "type": "object",
                            "properties": {
                                "hasLaptop": {"type": "boolean"},
                                "hasStableInternet": {"type": "boolean"}
                            }
                        },
                        "callOutcome": {
                            "type": "string",
                            "enum": ["Scheduled", "Follow_Up", "Not_Interested", "Wrong_Number"]
                        },
                        "nextSteps": {"type": "string"},
                        "callDuration": {"type": "number"},
                        "transcriptSummary": {"type": "string"}
                    },
                    "required": [
                        "studentName",
                        "studentGrade",
                        "parentName",
                        "callOutcome"
                    ]
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
                'location': mailing_address.split(',')[1].strip() if ',' in mailing_address else 'Unknown Location',
                'agent_name': agent,
                'source': source_name
            },
            'assistantOverrides': {
                'variableValues': {
                    'name': name,
                    'mailing_address': mailing_address,
                    'location': mailing_address.split(',')[1].strip() if ',' in mailing_address else 'Unknown Location',
                    'agent_name': agent
                },
                'context': json.dumps({
                    "customer_info": {
                        "name": name,
                        "mailing_address": mailing_address,
                        "source": source_name
                    },
                    "conversation_script": conversation_flow,
                    "course_info": {
                        "little_innovator": {
                            "grades": "1-2",
                            "modules": ["Little Innovator 1", "Little Innovator 2"],
                            "duration": "6 months per module",
                            "fee": "eighteen thousand rupees per module"
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
                            "fee": "twenty four thousand rupees per module"
                        }
                    }
                })
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
            
            # Start polling for call status
            polling_thread = threading.Thread(
                target=poll_call_status_and_process_transcript,
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

def extract_mom(call_data):
    """
    Extracts minutes of meeting from the provided call data.
    
    Parameters:
    - call_data: The JSON response from the API containing details about the call.

    Returns:
    - A string summarizing the minutes of meeting.
    """
    # Example implementation; customize based on your actual data structure
    return f"Summary of Call ID: {call_data.get('id')} - Details about discussion points and decisions made."

def extract_transcript(call_data):
    """
    Extracts the transcript from the provided call data.
    
    Parameters:
    - call_data: The JSON response from the API containing details about the call.

    Returns:
    - A string containing the transcript of the conversation.
    """
    # Example implementation; customize based on your actual data structure
    return "Transcript of the conversation goes here."

def save_mom_and_transcript(mom_summary, transcript_data):
    """
    Saves MoM and transcript data into text and JSON files in the current working directory.

    Parameters:
    - mom_summary: The summary of minutes of meeting.
    - transcript_data: The transcript of the conversation.
    """
    
    # Save MoM as a text file
    with open('call_mom.txt', 'w') as mom_file:
        mom_file.write(mom_summary)

    # Save transcript as a JSON file
    with open('call_transcript.json', 'w') as json_file:
        json.dump({"transcript": transcript_data}, json_file)

def extract_transcript(call_data):
    """
    Extracts the transcript from the provided call data.
    
    Parameters:
    - call_data: The JSON response from the API containing details about the call.

    Returns:
    - A string containing the transcript of the conversation.
    """
    # Example implementation; customize based on your actual data structure
    return "Transcript of the conversation goes here."

def save_mom_and_transcript(mom_summary, transcript_data):
    """
    Saves MoM and transcript data into text and JSON files.

    Parameters:
    - mom_summary: The summary of minutes of meeting.
    - transcript_data: The transcript of the conversation.
    """
    
    # Save MoM as a text file
    with open('call_mom.txt', 'w') as mom_file:
        mom_file.write(mom_summary)

    # Save transcript as a JSON file
    with open('call_transcript.json', 'w') as json_file:
        json.dump({"transcript": transcript_data}, json_file)

def poll_call_status_and_process_transcript(call_id, agent_id, name, phone_number, headers):
    try:
        transcript = []
        last_message_count = 0
        start_time = int(datetime.utcnow().timestamp() * 1000)
        
        print(f"\nCall URL: https://api.vapi.ai/calls/{call_id}\n")
        
        while True:
            response = requests.get(f'https://api.vapi.ai/call/{call_id}', headers=headers)
            
            if response.status_code == 200:
                call_data = response.json()
                current_status = call_data.get('status')
                print(f"\nCall Status: {current_status}")
                
                # Get messages
                messages_response = requests.get(f'https://api.vapi.ai/call/{call_id}/messages', headers=headers)
                if messages_response.status_code == 200:
                    messages = messages_response.json()
                    if len(messages) > last_message_count:
                        for msg in messages[last_message_count:]:
                            formatted_msg = {
                                "role": "bot" if msg.get('role') == 'assistant' else "user",
                                "text": msg.get('text', ''),
                                "timestamp": msg.get('timestamp', start_time),
                                "duration": msg.get('duration', 0)
                            }
                            transcript.append(formatted_msg)
                            print(f"\nNew Message from {formatted_msg['role']}:")
                            print(f"Content: {formatted_msg['text']}")
                        
                        last_message_count = len(messages)
                        
                        # Save transcript to file after each update
                        transcript_file = "transcript.json"
                        with open(transcript_file, 'w') as f:
                            json.dump({"messages": transcript}, f, indent=4)
                
                if current_status in ['completed', 'failed']:
                    print("\n=== Call Completed - Generating Analysis ===")
                    
                    # Generate final analysis
                    analysis = generate_call_analysis({"messages": transcript})
                    
                    # Save analysis to file
                    analysis_file = "call_analysis.json"
                    with open(analysis_file, 'w') as f:
                        json.dump(analysis, f, indent=4)
                    
                    print("\nTranscript saved to: transcript.json")
                    print("Analysis saved to: call_analysis.json")
                    print(f"Call Outcome: {analysis['structuredData']['callOutcome']}")
                    break
            
            time.sleep(2)
            
    except Exception as e:
        print(f"Error polling call status: {str(e)}")

def generate_transcript_summary(transcript_data):
    """Generate a summary from the transcript data."""
    try:
        # Extract conversation from transcript
        conversation = []
        for turn in transcript_data.get("turns", []):
            speaker = turn.get("speaker", "")
            text = turn.get("text", "")
            conversation.append(f"{speaker}: {text}")
        
        # Create a summary of key points
        summary = {
            "conversation_length": len(conversation),
            "key_points": extract_key_points(conversation),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return summary
        
    except Exception as e:
        print(f"Error generating transcript summary: {str(e)}")
        return {"error": str(e)}

def extract_key_points(conversation):
    """Extract key points from the conversation."""
    key_points = {
        "course_interest": [],
        "student_details": {},
        "scheduling_info": {},
        "concerns_raised": [],
        "next_steps": []
    }
    
    # Implement your logic to extract key points from the conversation
    # This could involve NLP, pattern matching, or other text analysis methods
    
    return key_points

def store_call_data(call_id, agent_id, customer_name, phone_number, transcript, summary, mom):
    """Store complete call data with MOM"""
    try:
        db = get_mongodb_connection()
        if not db:
            return False

        call_record = {
            'call_id': call_id,
            'agent_id': agent_id,
            'customer_name': customer_name,
            'phone_number': phone_number,
            'timestamp': datetime.now(),
            'transcript': transcript,
            'summary': summary,
            'mom': mom,
            'status': 'processed'
        }

        result = db.calls.update_one(
            {'call_id': call_id},
            {'$set': call_record},
            upsert=True
        )
        
        # Save local files
        save_transcript_to_file(call_id, transcript)
        
        # Save MOM files
        if mom:
            txt_filename = f"mom_{call_id}.txt"
            with open(txt_filename, 'w') as f:
                f.write(mom['text_version'])
            
            json_filename = f"mom_{call_id}.json"
            with open(json_filename, 'w') as f:
                json.dump(mom['structured_version'], f, indent=4)
        
        print(f"Full call data stored with MOM. MongoDB ID: {result.upserted_id}")
        return True
    except Exception as e:
        print(f"Error storing complete call data: {str(e)}")
        return False

def save_mom_to_file(self):
    """Save MOM to files in current working directory"""
    try:
        if not self.mom:
            return False

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        call_id = self.current_call_id or f"call_{timestamp}"
        
        # Save text version
        txt_filename = f"mom_{call_id}.txt"
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(self.mom['text_version'])
        
        # Save structured version
        json_filename = f"mom_{call_id}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.mom['structured_version'], f, indent=4)
        
        print(f"MOM saved to files: {txt_filename}, {json_filename}")
        return True
    except Exception as e:
        print(f"Error saving MOM to file: {str(e)}")
        return False

def generate_mom(transcript, customer_name, agent_id, call_time):
    """
    Generate a structured Minutes of Meeting (MoM) summary from the transcript.

    Parameters:
    - transcript: List of messages from call transcript.
    - customer_name: Name of the customer.
    - agent_id: ID of the agent handling the call.
    - call_time: Timestamp of the call.

    Returns:
    - Dictionary with structured MoM.
    """
    student_name = "Unknown"
    student_grade = "Unknown"
    key_discussions = []
    
    for message in transcript:
        text = message.get("message", "").lower()
        
        if "child's name is" in text:
            student_name = text.split("child's name is")[-1].strip().split(" ")[0]
        
        if "grade" in text:
            grade_match = re.search(r"grade (\d+)", text)
            if grade_match:
                student_grade = grade_match.group(1)

        if "robotics" in text:
            key_discussions.append("Interest in Robotics course")
        if "ai" in text or "artificial intelligence" in text:
            key_discussions.append("Interest in AI course")
        if "schedule" in text:
            key_discussions.append("Class scheduling was discussed")

    # Structure the MoM
    mom_data = {
        "call_id": agent_id,
        "timestamp": call_time.strftime("%Y-%m-%d %H:%M:%S"),
        "participants": {
            "agent": agent_id,
            "customer": customer_name,
            "student": student_name
        },
        "student_grade": student_grade,
        "key_discussion_points": key_discussions,
        "next_steps": ["Follow-up required for scheduling" if "schedule" not in key_discussions else "Session scheduled"]
    }

    return mom_data

def extract_student_info(text):
    """Extract student information from text."""
    if 'grade' in text:
        match = re.search(r'grade (\d+)', text)
        if match:
            return f"- Student's Grade: {match.group(1)}"
    return f"- {text.capitalize()}"

def extract_course_interest(text):
    """Extract course interest information from text."""
    interests = []
    if 'robotics' in text:
        interests.append('Robotics')
    if 'ai' in text or 'artificial intelligence' in text:
        interests.append('AI')
    if interests:
        return f"- Interested in: {', '.join(interests)}"
    return f"- {text.capitalize()}"

def extract_technical_info(text):
    """Extract technical setup information from text."""
    if 'laptop' in text:
        has_laptop = 'yes' in text or 'have' in text
        return f"- Laptop Available: {'Yes' if has_laptop else 'No'}"
    if 'internet' in text:
        has_internet = 'yes' in text or 'have' in text
        return f"- Stable Internet: {'Yes' if has_internet else 'No'}"
    return f"- {text.capitalize()}"

def extract_scheduling_info(text):
    """Extract scheduling information from text."""
    if 'schedule' in text:
        # Try to extract date and time
        date_match = re.search(r'\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', text, re.I)
        time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:am|pm))', text, re.I)
        if date_match and time_match:
            return f"- Session scheduled for {date_match.group(0)} at {time_match.group(0)}"
    return f"- {text.capitalize()}"

def generate_next_steps(mom):
    """Generate next steps based on discussion points."""
    next_steps = []
    
    if mom['discussion_points']['scheduling']:
        next_steps.append("- Send session confirmation email")
    
    if mom['discussion_points']['course_interests']:
        next_steps.append("- Share detailed course curriculum")
    
    if mom['discussion_points']['technical_setup']:
        next_steps.append("- Send technical requirements document")
    
    return "\n".join(next_steps) if next_steps else "- Follow up required for next steps"

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
        gr.Markdown("# UNPOD Call Interface")
        
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
    """Poll call status and process transcript when completed."""
    call_summary = CallSummary()
    try:
        recorder = None
        recording_task = None
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        start_time = int(time.time() * 1000)
        transcript = []
        last_message_count = 0
        current_status = None
        
        while True:
            # Get call status and details
            call_response = requests.get(f'https://api.vapi.ai/call/{call_id}', headers=headers)
            
            if call_response.status_code == 200:
                call_data = call_response.json()
                current_status = call_data.get('status')
                print(f"\nCall Status: {current_status}")
                
                # Update summary with final status
                call_summary.update_summary('call_outcome', current_status)
                
                # Get call details
                details_response = requests.get(f'https://api.vapi.ai/call/{call_id}/details', headers=headers)
                if details_response.status_code == 200:
                    details = details_response.json()
                    print("\n=== Call Details ===")
                    print(f"Call ID: {call_id}")
                    print(f"Start Time: {datetime.fromtimestamp(details.get('startTime', start_time)/1000).strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"Duration: {details.get('duration', 0):.2f}s")
                    print(f"Status: {details.get('status', 'Unknown')}")
                    print(f"Agent ID: {agent_id}")
                    print(f"Customer: {customer_name}")
                    print(f"Phone: {customer_number}")
                    print("===================")
                
                # Get call messages
                messages_response = requests.get(f'https://api.vapi.ai/call/{call_id}/messages', headers=headers)
                
                if messages_response.status_code == 200:
                    messages = messages_response.json()
                    
                    if len(messages) > last_message_count:
                        print("\n=== New Messages ===")
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
                            print(f"\nRole: {formatted_msg['role']}")
                            print(f"Message: {formatted_msg['message']}")
                            print(f"Time: {datetime.fromtimestamp(formatted_msg['time']/1000).strftime('%Y-%m-%d %H:%M:%S')}")
                            print(f"Duration: {formatted_msg['duration']/1000:.2f}s")
                        print("==================")
                        
                        last_message_count = len(messages)
                        
                        # Save transcript
                        save_transcript_to_mongodb(call_id, agent_id, customer_name, customer_number, transcript)
                        
                        # Generate analysis
                        mom_generator = MOMGenerator()
                        analysis = mom_generator.generate_dynamic_call_analysis({
                            'call_id': call_id,
                            'messages': messages,
                            'details': details if details_response.status_code == 200 else {}
                        })
                        
                        print("\n=== Call Analysis ===")
                        print(f"Summary: {analysis.get('summary', 'N/A')}")
                        
                        if analysis.get('structuredData', {}):
                            print("\nStructured Data:")
                            for key, value in analysis.get('structuredData', {}).items():
                                print(f"{key}: {value}")
                        print(f"\nEvaluation: {analysis.get('successEvaluation', 'N/A')}")
                        print("===================")
                        
                        # Extract messages for readable transcript
                        extracted_messages = transcript_extractor.extract_messages(transcript)
                        txt_path = transcript_extractor.generate_readable_transcript(extracted_messages, call_id, "txt")
                        json_path = transcript_extractor.generate_readable_transcript(extracted_messages, call_id, "json")
                        print(f"\nTranscript files generated:")
                        print(f"TXT: {txt_path}")
                        print(f"JSON: {json_path}")
                
                # Get call metrics if available
                metrics_response = requests.get(f'https://api.vapi.ai/call/{call_id}/metrics', headers=headers)
                if metrics_response.status_code == 200:
                    metrics = metrics_response.json()
                    print("\n=== Call Metrics ===")
                    print(f"Total Duration: {metrics.get('totalDuration', 0):.2f}s")
                    print(f"Speech Duration: {metrics.get('speechDuration', 0):.2f}s")
                    print(f"Silence Duration: {metrics.get('silenceDuration', 0):.2f}s")
                    print(f"Turn Count: {metrics.get('turnCount', 0)}")
                    print("===================")
                
                if current_status in ['completed', 'failed']:
                    print(f"\nCall {current_status.upper()}")
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

class MOMGenerator:
    def generate_mom(self, transcript_data, call_metadata):
        """Generate both structured and text versions of MoM"""
        try:
            structured_mom = self._generate_structured_mom(transcript_data, call_metadata)
            text_mom = self._generate_text_version(structured_mom)
            
            return {
                'structured_version': structured_mom,
                'text_version': text_mom
            }
            
        except Exception as e:
            print(f"Error generating MoM: {str(e)}")
            return None

    def _generate_structured_mom(self, transcript_data, call_metadata):
        """Generate structured MoM from transcript data and call metadata"""
        # Extract key information
        participants = {
            'agent': call_metadata.get('agent_id', 'Unknown'),
            'customer': call_metadata.get('customer_name', 'Unknown')
        }

        # Example structure, you can customize based on your needs
        return {
            "metadata": {
                "call_id": call_metadata.get('call_id', 'N/A'),
                "timestamp": datetime.now().isoformat(),
                "duration": self._calculate_call_duration(transcript_data),
                "participants": participants
            },
            "discussion_points": self._extract_discussion_points(transcript_data),
            "action_items": self._extract_action_items(transcript_data),
            "next_steps": self._generate_next_steps(transcript_data)
        }

    def _generate_text_version(self, structured_mom):
        """Convert structured MoM to readable text format"""
        text_output = f"MoM for Call ID: {structured_mom['metadata']['call_id']}\n"
        text_output += f"Date: {structured_mom['metadata']['timestamp']}\n"
        text_output += f"Duration: {structured_mom['metadata']['duration']} minutes\n\n"
        
        text_output += "Participants:\n"
        for role, name in structured_mom['metadata']['participants'].items():
            text_output += f"- {role.capitalize()}: {name}\n"
            
        text_output += "\nKey Discussion Points:\n"
        for point in structured_mom['discussion_points']:
            text_output += f"- {point}\n"
            
        text_output += "\nAction Items:\n"
        for action in structured_mom['action_items']:
            text_output += f"- {action}\n"
            
        text_output += "\nNext Steps:\n"
        for step in structured_mom['next_steps']:
            text_output += f"- {step}\n"
            
        return text_output

    def _extract_discussion_points(self, transcript):
        """Identify key discussion topics"""
        # Placeholder implementation
        return ["Discussed project timeline", "Reviewed budget"]

    def _extract_action_items(self, transcript):
        """Identify concrete action items"""
        # Placeholder implementation
        return ["Send follow-up email", "Schedule next meeting"]

    def _generate_next_steps(self, transcript):
        """Generate next steps based on action items"""
        # Placeholder implementation
        return ["Prepare project proposal", "Review action items"]

    def _calculate_call_duration(self, transcript):
        """Calculate call duration from timestamps"""
        if not transcript.get('messages'):
            return 0
        start = datetime.fromisoformat(transcript['messages'][0]['timestamp'])
        end = datetime.fromisoformat(transcript['messages'][-1]['timestamp'])
        return round((end - start).total_seconds() / 60, 2)  # Duration in minutes

    def extract_call_analysis(messages):
        """Extract and analyze call data from messages"""
        try:
            analysis = {
                "call_summary": "",
                "key_points": [],
                "action_items": [],
                "customer_info": {},
                "call_outcome": "pending"
            }
            
            # Process each message
            for msg in messages:
                text = msg.get('text', '').lower()
                role = msg.get('role', '')
                
                # Extract customer information
                if role == 'user':
                    if 'name' in text:
                        name_match = re.search(r'(?:my name is|this is) ([a-zA-Z\s]+)', text)
                        if name_match:
                            analysis['customer_info']['name'] = name_match.group(1).strip()
                    
                    if 'grade' in text:
                        grade_match = re.search(r'grade (\d+)', text)
                        if grade_match:
                            analysis['customer_info']['grade'] = grade_match.group(1)
                    
                    if 'location' in text or 'city' in text:
                        location_match = re.search(r'(?:in|from|at) ([a-zA-Z\s,]+)', text)
                        if location_match:
                            analysis['customer_info']['location'] = location_match.group(1).strip()
                
                # Extract key points and action items
                if role == 'assistant':
                    # Key points from agent's responses
                    if len(text) > 20:  # Meaningful responses
                        analysis['key_points'].append(text)
                    
                    # Action items
                    if any(word in text for word in ['will', 'shall', 'going to', 'plan to']):
                        analysis['action_items'].append(text)
            
            # Generate summary
            if analysis['customer_info']:
                customer_details = []
                if 'name' in analysis['customer_info']:
                    customer_details.append(f"Customer: {analysis['customer_info']['name']}")
                if 'grade' in analysis['customer_info']:
                    customer_details.append(f"Grade: {analysis['customer_info']['grade']}")
                if 'location' in analysis['customer_info']:
                    customer_details.append(f"Location: {analysis['customer_info']['location']}")
                
                analysis['call_summary'] = " | ".join(customer_details)
            
            return analysis
        except Exception as e:
            print(f"Error in call analysis: {str(e)}")
            return None

    def poll_call_status_and_process_transcript(call_id, agent_id, name, phone_number, headers):
        """Poll call status and process transcript when completed."""
        try:
            transcript = []
            last_message_count = 0
            start_time = int(datetime.utcnow().timestamp() * 1000)
            
            print(f"\nCall URL: https://api.vapi.ai/calls/{call_id}\n")
            
            while True:
                response = requests.get(f'https://api.vapi.ai/call/{call_id}', headers=headers)
                
                if response.status_code == 200:
                    call_data = response.json()
                    current_status = call_data.get('status')
                    print(f"\nCall Status: {current_status}")
                    
                    messages_response = requests.get(f'https://api.vapi.ai/call/{call_id}/messages', headers=headers)
                    if messages_response.status_code == 200:
                        messages = messages_response.json()
                        if len(messages) > last_message_count:
                            for msg in messages[last_message_count:]:
                                formatted_msg = {
                                    "role": "bot" if msg.get('role') == 'assistant' else "user",
                                    "text": msg.get('text', ''),
                                    "timestamp": msg.get('timestamp', start_time)
                                }
                                transcript.append(formatted_msg)
                                
                                # Print message details
                                print(f"\nNew Message from {formatted_msg['role']}:")
                                print(f"Content: {formatted_msg['text']}")
                                
                                # Real-time analysis of each message
                                if formatted_msg['role'] == 'user':
                                    text = formatted_msg['text'].lower()
                                    # Extract name
                                    if 'name' in text:
                                        name_match = re.search(r'(?:my name is|this is) ([a-zA-Z\s]+)', text)
                                        if name_match:
                                            print(f"Customer Name: {name_match.group(1).strip()}")
                                    # Extract grade
                                    if 'grade' in text:
                                        grade_match = re.search(r'grade (\d+)', text)
                                        if grade_match:
                                            print(f"Grade: {grade_match.group(1)}")
                                    # Extract location
                                    if 'location' in text or 'city' in text:
                                        location_match = re.search(r'(?:in|from|at) ([a-zA-Z\s,]+)', text)
                                        if location_match:
                                            print(f"Location: {location_match.group(1).strip()}")
                                
                            last_message_count = len(messages)
                    
                    # If call is completed or failed, show final analysis
                    if current_status in ['completed', 'failed']:
                        print("\n========= Final Call Analysis =========")
                        print(f"Call Status: {current_status}")
                        print(f"Total Messages: {len(transcript)}")
                        
                        # Analyze user messages
                        user_messages = [msg for msg in transcript if msg['role'] == 'user']
                        bot_messages = [msg for msg in transcript if msg['role'] == 'bot']
                        
                        print("\nCustomer Information:")
                        for msg in user_messages:
                            text = msg['text'].lower()
                            # Extract name
                            if 'name' in text:
                                name_match = re.search(r'(?:my name is|this is) ([a-zA-Z\s]+)', text)
                                if name_match:
                                    print(f"- Name: {name_match.group(1).strip()}")
                            # Extract grade
                            if 'grade' in text:
                                grade_match = re.search(r'grade (\d+)', text)
                                if grade_match:
                                    print(f"- Grade: {grade_match.group(1)}")
                            # Extract location
                            if 'location' in text or 'city' in text:
                                location_match = re.search(r'(?:in|from|at) ([a-zA-Z\s,]+)', text)
                                if location_match:
                                    print(f"- Location: {location_match.group(1).strip()}")
                        
                        print("\nKey Discussion Points:")
                        for msg in bot_messages:
                            text = msg['text'].lower()
                            if any(keyword in text for keyword in ['course', 'program', 'session', 'schedule', 'fee']):
                                print(f"- {msg['text']}")
                        
                        print("\nAction Items:")
                        for msg in bot_messages:
                            text = msg['text'].lower()
                            if any(word in text for word in ['will', 'shall', 'going to', 'schedule', 'book']):
                                print(f"- {msg['text']}")
                        
                        print("=====================================")
                        break
                
                time.sleep(2)
        except Exception as e:
            print(f"Error polling call status: {str(e)}")
            time.sleep(2)

if __name__ == "__main__":
    launch_gradio_interface()
