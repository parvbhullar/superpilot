import os
from twilio.rest import Client
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class TwilioManager:
    """Manages Twilio operations and call handling"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            # Get credentials from environment
            self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
            
            # Validate credentials
            if not all([self.account_sid, self.auth_token, self.phone_number]):
                missing = []
                if not self.account_sid:
                    missing.append("TWILIO_ACCOUNT_SID")
                if not self.auth_token:
                    missing.append("TWILIO_AUTH_TOKEN")
                if not self.phone_number:
                    missing.append("TWILIO_PHONE_NUMBER")
                print(f"Warning: Missing Twilio credentials: {', '.join(missing)}")
            else:
                try:
                    self.client = Client(self.account_sid, self.auth_token)
                    print("Twilio client initialized successfully")
                    print(f"Using phone number: {self.phone_number}")
                except Exception as e:
                    print(f"Error initializing Twilio client: {str(e)}")
                    self.client = None
            
            self.initialized = True

    def initiate_call(self, web_call_url, to_number, callback_url=None):
        """
        Initiate an outbound call using Twilio
        
        Args:
            web_call_url (str): URL for the VAPI web call
            to_number (str): Destination phone number
            callback_url (str, optional): URL for status callbacks
            
        Returns:
            tuple: (success (bool), call_sid (str) or error_message (str))
        """
        try:
            if not all([self.account_sid, self.auth_token, self.phone_number]):
                return False, "Missing Twilio credentials"

            call = self.client.calls.create(
                url=web_call_url,
                to=to_number,
                from_=self.phone_number,
                status_callback=callback_url or 'https://your-domain.com/call-status'
            )
            return True, call.sid

        except Exception as e:
            return False, f"Error initiating Twilio call: {str(e)}"

    def stop(self):
        """Stop the current call and clean up resources."""
        try:
            print("Stopping call...")
            if self._client:
                self._client.leave()  # Leave the call if connected
                print("Successfully left the call.")
            self._client = None
            print("Call stopped.")
        except Exception as e:
            print(f"Error stopping call: {e}")

    def end_call(self, call_sid):
        """
        End an active Twilio call
        
        Args:
            call_sid (str): The Twilio call SID to end
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            call = self.client.calls(call_sid).update(status='completed')
            return call.status == 'completed'
        except Exception as e:
            print(f"Error ending Twilio call: {e}")
            return False

    def get_call_status(self, call_sid):
        """
        Get the status of a Twilio call
        
        Args:
            call_sid (str): The Twilio call SID to check
            
        Returns:
            str: Call status or error message
        """
        try:
            call = self.client.calls(call_sid).fetch()
            return call.status
        except Exception as e:
            return f"Error fetching call status: {str(e)}"

    def get_call_duration(self, call_sid):
        """
        Get the duration of a completed call
        
        Args:
            call_sid (str): The Twilio call SID
            
        Returns:
            int: Call duration in seconds or -1 if error
        """
        try:
            call = self.client.calls(call_sid).fetch()
            return int(call.duration) if call.duration else -1
        except Exception as e:
            print(f"Error getting call duration: {e}")
            return -1

    def get_call_recording(self, call_sid):
        """
        Get the recording URL for a call
        
        Args:
            call_sid (str): The Twilio call SID
            
        Returns:
            str: Recording URL or None if not found
        """
        try:
            recordings = self.client.recordings.list(call_sid=call_sid)
            return recordings[0].uri if recordings else None
        except Exception as e:
            print(f"Error getting call recording: {e}")
            return None

    def format_phone_number(self, phone_number):
        """
        Format phone number to E.164 format
        
        Args:
            phone_number (str): Phone number to format
            
        Returns:
            str: Formatted phone number
        """
        # Remove any non-numeric characters
        cleaned = ''.join(filter(str.isdigit, phone_number))
        
        # Add country code if not present
        if len(cleaned) == 10:  # US number without country code
            return f"+1{cleaned}"
        elif len(cleaned) > 10:  # Assume it already has country code
            return f"+{cleaned}"
        return cleaned  # Return as is if format unknown