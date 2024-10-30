


#----------------------------------------------------------------
from collections.abc import Iterator
from langchain.schema.messages import BaseMessage
from langchain_core.messages import AIMessageChunk
from langchain_core.messages import HumanMessage
from llama_index.core.chat_engine import SimpleChatEngine
#from litellm import LiteLLM
from llama_index.llms.litellm import LiteLLM
from llama_index.core.llms import LLM

import asyncio
import re

from typing import Any, List, Dict, Optional,AsyncIterator
from openai import OpenAI

class SimpleAnswer:
    def __init__(self, config,question: str,docs: List[Any], persona: Dict[str, str], message_history: Optional[List[BaseMessage]] = None) -> None:
        self.question = question
        self.llm = self.load_litellm_as_llm(config)
        self.message_history = message_history or []
        self.docs = docs or []
        self.persona = persona
        self.index=None

    def _build_prompt(self, content: str) -> str:
        """Builds the prompt for the LLM based on the content and question."""
        prompt = f"{self.persona['persona']}.\n Answer the following question based on the content provided and persona you are based on:\n"
        prompt += f"Content: {content}\n"
        
        
        return prompt

    def load_litellm_as_llm(self,config):
        """
        Load LiteLLM as an LLM in LlamaIndex with the provided configuration.

        Args:
            config (dict): Configuration parameters for LiteLLM, such as model_name, temperature, etc.

        Returns:
            LLM: An instance of LiteLLM configured for use in LlamaIndex.
        """
        # Extract configuration parameters
        model_name = config.get('model_name', 'default_model')
        temperature = config.get('temperature', 0.7)
        max_tokens = config.get('max_tokens', 150)

        # Initialize LiteLLM with the specified configuration
        litellm_instance = LiteLLM(model_name=model_name, temperature=temperature, max_tokens=max_tokens)

        # Create an LLM instance for LlamaIndex
        llm_instance = litellm_instance

        return llm_instance

    
    async def response(self, prompt: str, query: str) -> str:
        """Fetch response from chat engine."""
        #self.index=self.llm_config(config=None)
        #llm_index=self.index
        chat_engine = SimpleChatEngine.from_defaults(llm=self.llm,system_prompt=prompt)
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
            limited_docs = self.docs
            for index, item in enumerate(limited_docs):
                content = clean_content(item.content)  # Clean content asynchronously
                prompt = self._build_prompt(content)
                response = await self.response(prompt=prompt, query=self.question)

                # Create citation in the desired format
                citation_key = str(index + 1)  # Start keys from 1
                citation_value = item.document_id 
                #yield await self.response(prompt=prompt, query=self.question)
                yield response, citation_key,citation_value

    # @property
    # async def llm_answer(self) -> AsyncIterator[str]:
    #     """Compiles the final answer from processed output."""
    #     async for packet in self._raw_output():
    #         yield packet 

    @property
    async def llm_answer(self) -> AsyncIterator[str]:
        """Compiles the final answer from processed output."""
        combined_answer = []
        citations_dict = {}

        async for response, citation_key, citation_value in self._raw_output():
            # Append the response along with its citation reference
            #print(f"Response [{citation_key}]: {response}")
            yield response
            await asyncio.sleep(2)
            print()
            combined_answer.append(f"{str(response)} [{citation_key}]")  # Format as "Response [1]"
            citations_dict[citation_key] = citation_value  # Add to citations dictionary

        # Prepare final output with responses and citations
        final_output = {
            "answers": "\n".join(combined_answer),
            "citations": citations_dict
        }

        # Prepare final output with responses and citations
        final_output = {
            "answers": "\n".join(combined_answer),
            "citations": citations_dict
        }
        
        yield final_output 

    def add_to_history(self, response: str) -> None:
        """Adds a response to the message history."""
        self.message_history.append(HumanMessage(content=response))

def clean_content(content: str) -> str:
    """Cleans the input content."""
    cleaned = content.strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.replace('{', '').replace('}', '')
    return cleaned

