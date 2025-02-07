from flask import Flask, send_from_directory, jsonify, request
from livekit import api
import os
from dotenv import load_dotenv
import logging
import json

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='')

# LiveKit configuration - hardcoded for testing
api_key = 'APIH2yT5t8Zrcay'
api_secret = 'yuBQP76ZqxVVBDL4PbVZE10kDXRydKZQcCeNg2p83yG'
livekit_url = 'wss://unpod-ouwdr76k.livekit.cloud'

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/get-token', methods=['POST'])
def get_token():
    try:
        data = request.json
        logger.info(f"Received token request with data: {data}")
        
        name = data.get('name', '')
        room_name = 'test-room'
        
        # Create access token with metadata
        at = api.AccessToken(api_key, api_secret)
        at.name = name
        at.identity = name
        
        # Set metadata directly on the token
        metadata = json.dumps(data)
        at.metadata = metadata
        logger.info(f"Setting metadata on token: {metadata}")
        
        # Add room permissions with metadata
        grant = {
            "room": room_name,
            "roomJoin": True,
            "canPublish": True,
            "canSubscribe": True,
            "metadata": metadata  # Include metadata in the grant
        }
        at.grant = grant
        
        # Generate token
        token = at.to_jwt()
        logger.info(f"Generated token for user {name} with metadata")
        
        # Return token with metadata
        return jsonify({
            'token': token,
            'url': livekit_url,
            'room': room_name,
            'metadata': metadata  # Include metadata in response
        })
    except Exception as e:
        logger.error(f"Error generating token: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
