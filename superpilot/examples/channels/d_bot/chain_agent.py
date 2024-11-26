import logging
import os
import nest_asyncio
from dotenv import load_dotenv
import work.superpilot.superpilot.examples.channels.d_bot.discord as discord
from discord.ext import commands
from langchain.chat_models import ChatOpenAI  
from langchain.agents import initialize_agent, AgentType, Tool
from langchain_community.llms import OpenAI  
from datetime import datetime

load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

nest_asyncio.apply()

discord_token = os.getenv("DISCORD_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")

if not discord_token:
    raise ValueError("Please set the DISCORD_TOKEN environment variable in your .env file.")

if not openai_api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable in your .env file.")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  
bot = commands.Bot(command_prefix='!', intents=intents)

llm = ChatOpenAI(model="gpt-3.5-turbo", api_key=openai_api_key)

tools = [
    Tool(
        name="ChatAgent",
        func=lambda q: llm.invoke([q]),  
        description="Generate a response to the user's message."
    )
]

agent = initialize_agent(
    tools=tools,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    llm=llm,
    verbose=True,
)

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user}')

@bot.event
async def on_message(message: discord.Message):
    logger.info(f"Received message: {message.content}")

    if message.author.bot:
        return

    if message.content.startswith('!ask'):
        user_query = message.content[5:].strip()  
    else:
        user_query = message.content.strip()

    if not user_query:
        await message.channel.send("Please provide a question.")
        return

    try:
        logger.info(f"Running agent with query: {user_query}")
        response = agent.invoke([user_query])
        logger.info(f"Agent response: {response}")

        if response:
            await message.channel.send(response.get('output', "Sorry, I couldn't generate a response."))
        else:
            await message.channel.send("I'm sorry, I couldn't generate a response.")
    except Exception as e:
        await message.channel.send("An error occurred while generating a response.")
        logger.error(f"Error generating response: {e}")


if __name__ == "__main__":
    try:
        bot.run(discord_token)
    except Exception as e:
        logger.error(f"Error running Discord bot: {e}")

