


#----------------------------------------------------------------
from collections.abc import Iterator
from langchain.schema.messages import BaseMessage
from langchain_core.messages import AIMessageChunk
from langchain_core.messages import HumanMessage
from llama_index.core.chat_engine import SimpleChatEngine

import asyncio
import re

from typing import Any, List, Dict, Optional,AsyncIterator
from openai import OpenAI

class SimpleAnswer:
    def __init__(self, question: str,docs: List[Any], persona: Dict[str, str], message_history: Optional[List[BaseMessage]] = None) -> None:
        self.question = question
        self.llm = "gpt-4o"
        self.message_history = message_history or []
        self.docs = docs or []
        self.persona = persona

    def _build_prompt(self, content: str) -> str:
        """Builds the prompt for the LLM based on the content and question."""
        prompt = f"{self.persona['persona']}.\n Answer the following question based on the content provided and persona you are based on:\n"
        prompt += f"Content: {content}\n"
        
        
        return prompt

    async def response(self, prompt: str, query: str) -> str:
        """Fetch response from chat engine."""
        chat_engine = SimpleChatEngine.from_defaults(system_prompt=prompt)
        response = chat_engine.chat(query)
        return response

    async def fetch_response(self, prompt: str) -> str:
        """Fetch response from OpenAI based on the constructed prompt."""
        client = OpenAI()  # Ensure you have your OpenAI API client set up
        response_content = ""

        # Create a completion request
        response = await client.chat.completions.create(
            model=self.llm,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
        )
        
        message = response.choices[0].message
        response_content = message.content
        return response_content

    async def _raw_output(self) -> AsyncIterator[str]:
        """Generates output from the LLM based on the constructed prompts for each content."""
        if self.docs:
            limited_docs = self.docs[:10]
            for item in limited_docs:
                content = clean_content(item.content)  # Clean content asynchronously
                prompt = self._build_prompt(content)
                yield await self.response(prompt=prompt, query=self.question)

    @property
    async def llm_answer(self) -> AsyncIterator[str]:
        """Compiles the final answer from processed output."""
        async for packet in self._raw_output():
            yield packet 

    def add_to_history(self, response: str) -> None:
        """Adds a response to the message history."""
        self.message_history.append(HumanMessage(content=response))

def clean_content(content: str) -> str:
    """Cleans the input content."""
    cleaned = content.strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.replace('{', '').replace('}', '')
    return cleaned

