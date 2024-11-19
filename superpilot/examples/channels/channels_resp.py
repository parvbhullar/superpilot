import logging
import sys
import os
import nest_asyncio
from discord.ext import commands
import discord
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.memory import ChatMemoryBuffer
from datetime import datetime
import asyncio
from base import BaseChannel

sys.path.append("/Users/zestgeek31/Desktop/super-pilot/work/superpilot/superpilot/examples/channels")
from models import DocumentManager, ChatEngineManager, DatabaseHandler

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

class DiscordBot(discord.ext.commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_engine_manager = ChatEngineManager()
        self.load_documents()

    def load_documents(self):
        documents = DocumentManager.load_documents()
        self.chat_engine_manager.initialize_chat_engine(documents)

    async def on_message(self, message):
        if message.author.bot:
            return

        try:
            response = self.chat_engine_manager.get_response(message.content)

            await message.channel.send(response.response)

            DatabaseHandler.store_message_in_db(
                message.content, response.response, message.author.name, message.channel.id
            )
            logging.info(f"Responded to message: {message.content}")
        except Exception as e:
            logging.error(f"Error generating response: {e}")

def main():
    bot = DiscordBot(command_prefix="!", intents=intents)
    bot.run(discord_token)

if __name__ == "__main__":
    main()
