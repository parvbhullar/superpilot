"""
VAPI Call System Models and Core Implementation
"""

import os
import requests
import json
from datetime import datetime
import threading
import pyaudio
import wave
from pymongo import MongoClient
from bson import Binary
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VapiCall:
    """Core VAPI call implementation"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            # API setup
            self.api_key = os.getenv('VAPI_API_KEY', "8c3e405d-060c-4497-9ee5-67b5a62505ce")
            self.api_url = os.getenv('VAPI_API_URL', "https://api.vapi.ai")
            self.assistant_id = os.getenv('VAPI_ASSISTANT_ID')

            # Audio recording setup
            self.setup_audio_recording()
            
            # MongoDB setup
            self.setup_mongodb()
            
            # State tracking
            self.contact_name = None
            self.contact_number = None
            self.current_call_id = None
            
            self.initialized = True

    def setup_audio_recording(self):
        """Initialize audio recording settings"""
        self.audio_recording = []
        self.is_recording = False
        self.recording_thread = None
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 16000
        self.audio_dir = "recorded_conversations"
        os.makedirs(self.audio_dir, exist_ok=True)

        try:
            self.audio = pyaudio.PyAudio()
            input_device_index = int(os.getenv('AUDIO_INPUT_DEVICE_INDEX', 2))
            self.stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
                input_device_index=input_device_index
            )
            print("Audio recording initialized successfully")
        except Exception as e:
            print(f"Error initializing audio: {e}")
            self.audio = None

    def setup_mongodb(self):
        """Initialize MongoDB connection"""
        try:
            mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
            mongodb_db = os.getenv('MONGODB_DB', 'vapi-script')
            self.mongo_client = MongoClient(mongodb_uri)
            self.db = self.mongo_client[mongodb_db]
            self.transcript_collection = self.db["transcripts"]
            self.audio_collection = self.db["audio_recordings"]
            self.contacts_collection = self.db["contacts"]
            self.web_calls_collection = self.db["web_calls"]
            print("MongoDB connected successfully")
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            self.mongo_client = None

    def start_recording(self):
        """Start recording audio"""
        if self.is_recording:
            return
        
        self.is_recording = True
        self.audio_recording = []
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.start()

    def _record_audio(self):
        """Record audio in a separate thread"""
        while self.is_recording:
            try:
                data = self.stream.read(self.CHUNK)
                self.audio_recording.append(data)
            except Exception as e:
                print(f"Error recording audio: {e}")
                break

    def stop_recording(self):
        """Stop recording audio"""
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()
        return self.save_recording()

    def save_recording(self):
        """Save the current recording"""
        if not self.audio_recording:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.audio_dir}/call_{timestamp}.wav"
        
        try:
            wf = wave.open(filename, 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.audio_recording))
            wf.close()
            
            # Save to MongoDB
            if self.mongo_client:
                with open(filename, 'rb') as audio_file:
                    self.audio_collection.insert_one({
                        'call_id': self.current_call_id,
                        'timestamp': datetime.now(),
                        'audio_data': Binary(audio_file.read()),
                        'filename': filename
                    })
            
            self.audio_recording = []
            return filename
        except Exception as e:
            print(f"Error saving recording: {e}")
            return None

    def start(self, *, assistant_id=None):
        """Start a VAPI call"""
        try:
            url = f"{self.api_url}/call"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'assistant_id': assistant_id or self.assistant_id,
                'contact': {
                    'name': self.contact_name,
                    'phone_number': self.contact_number
                }
            }
            
            print(f"Starting call with payload: {payload}")
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            self.current_call_id = data.get('id')
            web_call_url = data.get('webCallUrl')
            
            # Start recording
            self.start_recording()
            
            # Save call details
            if self.mongo_client:
                self.web_calls_collection.insert_one({
                    'call_id': self.current_call_id,
                    'web_call_url': web_call_url,
                    'timestamp': datetime.now(),
                    'contact_name': self.contact_name,
                    'contact_number': self.contact_number
                })
            
            return self.current_call_id, web_call_url
            
        except Exception as e:
            print(f"Error starting call: {e}")
            return None, None

    def stop(self):
        """Stop the current call"""
        if self.current_call_id:
            try:
                url = f"{self.api_url}/call/{self.current_call_id}/end"
                headers = {'Authorization': f'Bearer {self.api_key}'}
                response = requests.post(url, headers=headers)
                response.raise_for_status()
                
                self.stop_recording()
                
                self.current_call_id = None
                return True
            except Exception as e:
                print(f"Error stopping call: {e}")
                return False
        return False

    def save_contact(self, name, number):
        """Save contact details"""
        if not (name or number):
            return False
            
        try:
            if self.mongo_client:
                self.contacts_collection.insert_one({
                    'name': name,
                    'number': number,
                    'timestamp': datetime.now()
                })
            return True
        except Exception as e:
            print(f"Error saving contact: {e}")
            return False

    def process_csv(self, file_path, remarks=None):
        """Process CSV file with contacts"""
        try:
            df = pd.read_csv(file_path)
            results = []
            
            for _, row in df.iterrows():
                name = row.get('name', '')
                number = row.get('phone', '')
                if self.save_contact(name, number):
                    results.append({'name': name, 'number': number})
                    
            return results
        except Exception as e:
            print(f"Error processing CSV: {e}")
            return []