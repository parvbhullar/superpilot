import os
import sys
import work.superpilot.superpilot.examples.channels.d_bot.discord as discord
from dotenv import load_dotenv
from discord.ext import commands
sys.path.append('/Users/zestgeek31/Desktop/super-pilot/work/superpilot/superpilot/examples/channels')
from work.superpilot.superpilot.examples.channels.d_bot.message_db import mongo_db_instance
import logging
sys.path.append('/Users/zestgeek31/Desktop/super-pilot/work/superpilot/superpilot/examples/channels')
from channels_resp import DiscordBot  

load_dotenv()

def main():
    discord_token = os.getenv("DISCORD_TOKEN")
    if discord_token is None:
        raise ValueError("Please set the DISCORD_TOKEN environment variable in your .env file.")

    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True 

    bot = DiscordBot(command_prefix='!', intents=intents)

    try:
        bot.run(discord_token)
    except Exception as e:
        logging.error(f"Error running Discord bot: {e}")

if __name__ == "__main__":
    main()
