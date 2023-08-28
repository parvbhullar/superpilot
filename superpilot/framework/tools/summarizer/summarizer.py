from __future__ import annotations

import logging
import asyncio

from superpilot.framework.helpers.processing.text import summarize_text
from concurrent.futures import ThreadPoolExecutor
from superpilot.core.configuration import get_config

executor = ThreadPoolExecutor()


class Summarizer:
    """
    """
    def __init__(self, config=None, run_func=None):
        self.config = config or get_config()
        self.run_func = run_func

    async def run(self, content: str, question: str, url:str= None) -> str:
        """Browse a website and return the answer and links to the user

        Args:
            url (str): The url of the website to browse
            question (str): The question asked by the user
            websocket (WebSocketManager): The websocket manager

        Returns:
            str: The answer and links to the user
        """
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=8)

        try:
            summary_text = await loop.run_in_executor(executor, self.summarize_text, content, question, url)

            return f"Information gathered from url {url}: {summary_text}"
        except Exception as e:
            print(f"An error occurred while processing the url {url}: {e}")
            raise e
            return f"Error processing the url {url}: {e}"

    def summarize_text(
            self, text: str, question: str, url: str
    ) -> str:
        """Summarize text using the OpenAI API

        Args:
            text (str): The text to summarize
            question (str): The question to ask the model
            url (str): The url of the text

        Returns:
            str: The summary of the text
        """
        if not text:
            return "Error: No text to summarize"

        summary, chunks = summarize_text(text, self.config, question=question)
        summary = f"Question: {question}\n Source: {url}\n Content summary part#: {summary}"

        print(summary)
        return summary