import json
import os
from datetime import datetime

class TranscriptExtractor:
    def __init__(self):
        self.transcript_dir = "transcripts"
        os.makedirs(self.transcript_dir, exist_ok=True)

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
            
            # Save to file
            filename = f"transcript_{timestamp}.txt"
            filepath = os.path.join(self.transcript_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(output)
            
            return filepath
        
        elif output_format == "json":
            output = {
                "generated_at": timestamp,
                "messages": messages
            }
            
            # Save to file
            filename = f"transcript_{timestamp}.json"
            filepath = os.path.join(self.transcript_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2)
            
            return filepath

    def process_transcript_file(self, transcript_file_path, output_format="txt"):
        """
        Process a transcript file and generate formatted output
        """
        try:
            with open(transcript_file_path, "r", encoding="utf-8") as f:
                transcript_data = json.load(f)
            
            messages = self.extract_messages(transcript_data)
            return self.generate_readable_transcript(messages, output_format)
            
        except Exception as e:
            print(f"Error processing transcript file: {str(e)}")
            return None

def main():
    # Example usage
    extractor = TranscriptExtractor()
    
    # Example with a transcript file
    transcript_file = "transcript.json"  # Replace with your transcript file path
    if os.path.exists(transcript_file):
        # Generate both TXT and JSON formats
        txt_output = extractor.process_transcript_file(transcript_file, "txt")
        json_output = extractor.process_transcript_file(transcript_file, "json")
        
        print(f"Generated TXT transcript: {txt_output}")
        print(f"Generated JSON transcript: {json_output}")
    else:
        print(f"Transcript file {transcript_file} not found")

if __name__ == "__main__":
    main()
