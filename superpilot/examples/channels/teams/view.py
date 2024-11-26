import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from db import save_message
from models import generate_response
from base import bot
# Load environment variables from .env file
load_dotenv('.env')

# Setup logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlackBotView:
    def __init__(self, bot_token, app_token):
        self.bot_token = bot_token
        self.app_token = app_token
        self.app = App(token=self.bot_token)

    def message_handler(self, message, say, logger):
        try:
            logger.info(f"Received message: {message}")
            
            user_message = message['text']
            output = generate_response(user_message)
            
            logger.info(f"Generated response: {output}")
            
            say(output)  # Send the response back to Slack
            save_message(user_message, output)  # Save the message to the database
        except Exception as e:
            logger.error(f"Error in message handler: {e}", exc_info=True)
            say("Sorry, something went wrong. Please try again later.")  # Send a generic error message to Slack

    def start(self):
        try:
            # Attach the message handler to the app
            self.app.message(".*")(self.message_handler)
            
            # Start the app using SocketModeHandler
            SocketModeHandler(self.app, self.app_token).start()
        except Exception as e:
            logger.error(f"Error starting the app: {e}", exc_info=True)
