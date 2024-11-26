# db.py

from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv('.env')

MONGO_URI = os.environ.get("MONGO_URI")  
client = MongoClient(MONGO_URI)
db = client['slack_bot_db']  
messages_collection = db['messages']  

def save_message(user_message, bot_response):
    """Saves the conversation to MongoDB."""
    from datetime import datetime

    message_data = {
        "timestamp": datetime.utcnow(),
        "user_message": user_message,
        "bot_response": bot_response
    }

    messages_collection.insert_one(message_data)
    print("Message saved to MongoDB.")
