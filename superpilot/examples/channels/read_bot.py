# main.py

import logging
import sys
import os
import nest_asyncio
from dotenv import load_dotenv
from llama_index.readers.discord import DiscordReader
import sys
sys.path.append('/Users/zestgeek31/Desktop/super-pilot/work/superpilot/superpilot/examples/channels')
from message_db import mongo_db_instance 

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

# Apply nest_asyncio to allow nested event loops (useful in Jupyter Notebooks)
nest_asyncio.apply()

# Load your Discord bot token from environment variables
discord_token = os.getenv("DISCORD_TOKEN")

# Check if the token is set
if discord_token is None:
    raise ValueError("Please set the DISCORD_TOKEN environment variable in your .env file.")

channel_ids = [1306234586304614400] 

try:
    documents = DiscordReader(discord_token=discord_token).load_data(channel_ids=channel_ids)
    logging.info(f"Fetched {len(documents)} documents from Discord.")
except Exception as e:
    logging.error(f"Error loading data from Discord: {e}")
    sys.exit(1)

bulk_messages = []

if documents:
    for doc in documents:
        logging.info(f"Processing document: {doc}")  # Log the entire document for debugging

        message_content = doc.text if hasattr(doc, 'text') else None 
        print("this is msg content-->", message_content)

        if isinstance(message_content, str):  
            message_content = message_content.strip()  # Strip extra spaces
            
            if message_content:  
                message_data = {
                    "content": message_content,
                    "author": {
                        "name": doc.metadata['username'] if 'username' in doc.metadata else "Unknown",
                        "bot": False 
                    },
                    "channel_id": doc.metadata['message_id'],  # Using message_id as channel_id for example
                    "timestamp": doc.metadata['created_at'].isoformat() if 'created_at' in doc.metadata else None
                }
                
                bulk_messages.append(message_data)
                print(bulk_messages)

    if bulk_messages:
        try:
            mongo_db_instance.get_collection().insert_many(bulk_messages) 
            logging.info(f"Successfully saved {len(bulk_messages)} messages to MongoDB.")
        except Exception as e:
            logging.error(f"Error saving messages to MongoDB: {e}")
else:
    logging.error("No messages were fetched.")