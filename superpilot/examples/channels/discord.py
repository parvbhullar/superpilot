import logging
import sys
import os
import nest_asyncio
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.memory import ChatMemoryBuffer
import discord
from discord.ext import commands
from message_db import mongo_db_instance  
from datetime import datetime
from llama_index.readers.discord import DiscordReader


discord_token = os.getenv("DISCORD_TOKEN")
if discord_token is None:
    raise ValueError("Please set the DISCORD_TOKEN environment variable in your .env file.")

class DiscordChannel(DiscordReader):
    def __init__(self, discord_token):
        super().__init__(discord_token)
        self.bot = None
        self.chat_engine = None

    def load_data(self, channel_ids):
        """ Fetch messages from Discord channels using the parent class's method """
        try:
            documents = super().load_data(channel_ids=channel_ids)
            return documents
        except Exception as e:
            raise ValueError(f"Error while fetching data from Discord: {e}")

    def setup_bot(self):
        """ Set up the Discord bot and its event loop """
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='!', intents=intents)

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

        index = VectorStoreIndex.from_documents(documents)
        memory = ChatMemoryBuffer.from_defaults(token_limit=1500)

        self.chat_engine = index.as_chat_engine(
            chat_mode="context",
            memory=memory,
            system_prompt=(
                "You are a chatbot that can have normal interactions and discuss various topics. "
                "You should also utilize historical Discord messages for context."
            ),
        )

    def store_message_in_db(self, user_message, bot_response, author, channel_id):
        """ Store user messages and bot responses into MongoDB """
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

    async def on_message(self, message):
        """ Bot event to handle incoming messages """
        if message.author.bot:
            return

        try:
            response = self.chat_engine.chat(message.content)

            await message.channel.send(response.response)

            self.store_message_in_db(message.content, response.response, message.author.name, message.channel.id)
            logging.info(f"Responded to message: {message.content}")
        except Exception as e:
            logging.error(f"Error generating response: {e}")

    def run(self):
        """ Run the bot """
        if self.bot:
            try:
                self.bot.run(discord_token)
            except Exception as e:
                logging.error(f"Error running Discord bot: {e}")
        else:
            logging.error("Bot is not set up yet. Call setup_bot() first.")

