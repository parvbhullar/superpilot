import logging
import sys
import os
import nest_asyncio
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.memory import ChatMemoryBuffer
import discord
from discord.ext import commands
from message_db import mongo_db_instance  
from datetime import datetime  

load_dotenv()

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

nest_asyncio.apply()

discord_token = os.getenv("DISCORD_TOKEN")
if discord_token is None:
    raise ValueError("Please set the DISCORD_TOKEN environment variable in your .env file.")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

# Fetch messages from MongoDB and convert them to LlamaIndex documents
bulk_messages = list(mongo_db_instance.get_collection().find())
documents = []

for msg in bulk_messages:
    if 'content' in msg and isinstance(msg['content'], str):
        author_name = 'Unknown'
        if isinstance(msg.get('author'), dict):
            author_name = msg['author'].get('name', 'Unknown')
        elif isinstance(msg.get('author'), str): 
            author_name = msg['author']
        
        documents.append(Document(
            text=msg['content'],
            metadata={
                'author': author_name,
                'timestamp': msg.get('timestamp', ''),
                'channel_id': msg.get('channel_id', '')
            }
        ))

if not documents:
    logging.warning("No documents found in MongoDB. The chat engine might not respond effectively.")

# Create the VectorStoreIndex and ChatMemoryBuffer for the chat engine
index = VectorStoreIndex.from_documents(documents)
memory = ChatMemoryBuffer.from_defaults(token_limit=1500)

chat_engine = index.as_chat_engine(
    chat_mode="context",
    memory=memory,
    system_prompt=(
        "You are a chatbot that can have normal interactions and discuss various topics. "
        "You should also utilize historical Discord messages for context."
    ),
)

# Store user messages and bot responses into MongoDB
def store_message_in_db(user_message, bot_response, author, channel_id):
    try:
        collection = mongo_db_instance.get_collection()
        document = {
            'content': user_message,
            'response': bot_response,
            'author': author,
            'channel_id': channel_id,
            'timestamp': str(datetime.now()) 
        }
        collection.insert_one(document)  
        logging.info(f"Stored message and response for author {author} in channel {channel_id}")
    except Exception as e:
        logging.error(f"Error storing message in MongoDB: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    try:
        # Generate a response using the chat engine
        response = chat_engine.chat(message.content)

        # Send the response back to Discord channel
        await message.channel.send(response.response)

        # Store user message and bot response in the database
        store_message_in_db(message.content, response.response, message.author.name, message.channel.id)
        logging.info(f"Responded to message: {message.content}")
    except Exception as e:
        logging.error(f"Error generating response: {e}")

if __name__ == "__main__":
    try:
        bot.run(discord_token)
    except Exception as e:
        logging.error(f"Error running Discord bot: {e}")
