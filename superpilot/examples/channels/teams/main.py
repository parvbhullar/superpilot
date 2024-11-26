from view import SlackBotView
import os

from dotenv import load_dotenv
from base import bot

load_dotenv('.env')

class SlackBot(SlackBotView):
    def __init__(self):
        bot_token = os.environ.get("SLACK_BOT_TOKEN")
        app_token = os.environ["SLACK_APP_TOKEN"]
        
        super().__init__(bot_token, app_token)

    def main(self):
        self.start()

if __name__ == "__main__":
    bot = SlackBot()
    bot.main()
