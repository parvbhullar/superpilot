"""
Base Module for VAPI Call System
Contains core functionality and base classes
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from twl import TwilioManager

# Load environment variables
load_dotenv()

class VapiBase:
    """Base class for VAPI functionality"""
    
    def __init__(self):
        self.twilio = TwilioManager()
        self.api_key = os.getenv('VAPI_API_KEY')
        self.api_url = os.getenv('VAPI_API_URL', 'https://api.vapi.ai')
        self.current_call_id = None
        self.conversation = []
        
    def start_call(self, call_id):
        """Start tracking a call"""
        self.current_call_id = call_id
        
    def end_call(self):
        """End current call"""
        self.current_call_id = None
        self.conversation = []
        
    def forward_call(self, target_agent_id):
        """Forward call to another agent"""
        if not self.current_call_id:
            return False
            
        try:
            url = f"{self.api_url}/call/{self.current_call_id}/forward"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            payload = {'assistant_id': target_agent_id}
            
            response = requests.post(url, headers=headers, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"Error forwarding call: {e}")
            return False
        
    def handle_call_event(self, event_type, data):
        """Handle call events"""
        if event_type == "transcription":
            self.conversation.append({
                'timestamp': datetime.now().isoformat(),
                'type': event_type,
                'data': data
            })
            
    def get_call_history(self):
        """Get conversation history"""
        return self.conversation