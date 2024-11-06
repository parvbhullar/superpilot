

from collections.abc import Iterator
from langchain.schema.messages import BaseMessage
from langchain_core.messages import AIMessageChunk
from langchain_core.messages import HumanMessage

import asyncio

from typing import Any
from openai import OpenAI
class SimpleAnswer:
    def __init__(self, question: str, llm,docs :list, persona:dict,message_history: list[BaseMessage] | None = None) -> None:
        self.question = question
        self.llm = "gpt-4o"
        self.message_history = message_history or []
        self._streamed_output: list[str] | None = None
        self.docs=docs or []
        self.persona=persona

    def _build_prompt(self, content: str) -> str:
        """Builds the prompt for the LLM based on the content and question."""
        prompt = f"For Question: {self.question}"
        prompt += f"{self.persona['persona']}.\n Answer the following question based on the content provided and persona you are based on:\n"
        prompt += f"Content:{content}\n"
        
        
        if self.persona:
            prompt += f"\nPersona: {self.persona['persona']}"
        return prompt

    def fetch_response(self, prompt: str) -> str:
        """Fetch response from OpenAI based on the constructed prompt."""
        client = OpenAI()  # Ensure you have your OpenAI API client set up
        response_content = ""

        # Create a completion request
        response = client.chat.completions.create(
            model=self.llm,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            
        )
        message=response.choices[0].message
        #print()
        # Collecting the response from the stream
          # Accumulate the response content
        response_content=message.content
        #print("After",response_content)
        return response_content

    def _raw_output(self) -> str:
        """Generates output from the LLM based on the constructed prompts for each content."""
        responses = []  # Store individual responses
        print("length of docs",len(self.docs))
        if self.docs:
            limited_docs = self.docs[:10]
            tasks = []  # List to hold all tasks
            for item in limited_docs:
                content = clean_content(item.content)  # Clean content asynchronously
                prompt = self._build_prompt(content)
                tasks.append(self.fetch_response(prompt))  # Append task to list
            
        #     # Gather all responses concurrently
        #     print("All responses")
        #     responses = await asyncio.gather(*tasks)

        # # Combine all responses into a final content
        # print("Number of Responses",len(responses))
        # print()
        # print("Final Response")
        # final_response = "\n".join(responses)
        # client = OpenAI()  # Ensure you have your OpenAI API client set up
        # response_content = ""
        # prompt=f"Gather all responses concurrently and give 5 combined responses on the behaviour of {self.persona['persona']} using the given responses:\n{final_response}"
        # # Create a completion request
        # response = client.chat.completions.create(
        #     model=self.llm,
        #     messages=[
        #         {"role": "system", "content": f'{self.persona["persona"]}'},
        #         {"role": "user", "content": prompt}
        #     ],
            
        # )
        # message=response.choices[0].message
        # print()
        # # Collecting the response from the stream
        #   # Accumulate the response content
        # response_content=message.content
        print("Tasks Returned")
        return tasks  # Return final response as needed
    
    @property
    def processed_streamed_output(self) -> Iterator[str]:
        """Processes streamed output from the LLM."""
        print("In Processed Streamed")
        if self._streamed_output is None:
            self._streamed_output = self._raw_output()
        for packet in self._streamed_output:
            yield packet

    @property
    def llm_answer(self)-> str:
        """Compiles the final answer from processed output."""
        print("In LLM Answer: ")
        answer = ""
        packets=self.processed_streamed_output
        for packet in self.processed_streamed_output:
            #print("Packet", type(packet))
            answer += packet  # Concatenate each string to answer
        print(type(answer))
        return answer
    def add_to_history(self, response: str) -> None:
        """Adds a response to the message history."""
        self.message_history.append(HumanMessage(content=response))



import re
def clean_content(content: str) -> str:
    # Remove leading and trailing whitespace
    cleaned = content.strip()
    # Remove extra new lines and spaces in the middle
    cleaned = re.sub(r'\s+', ' ', cleaned)
    #cleaned = content.strip()
    # Replace '{' and '}' with empty strings
    cleaned = cleaned.replace('{', '').replace('}', '')
    return cleaned

