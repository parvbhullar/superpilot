import os
import sys
import asyncio
import time
import io
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from abc import abstractmethod
from typing import IO, Any
from chardet.universaldetector import UniversalDetector
from email.parser import Parser,BytesParser
from openai import OpenAI
from email import policy
from pathlib import Path


from superpilot.core.pilot import SuperPilot
from superpilot.core.callback.handler.simple import SimpleCallbackHandler
from superpilot.core.callback.manager.std_io import STDInOutCallbackManager

from superpilot.core.state.base import State
from superpilot.core.state.pickle import PickleState


from superpilot.core.pilot.chain.strategy.observation_strategy import ObserverPrompt
from superpilot.core.pilot.chain.super import SuperChain
from typing import List
from superpilot.core.context.schema import Context, Event, Message, FileContentItem
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.examples.executor.base import BaseExecutor
from superpilot.examples.ed_tech.question_solver import QuestionSolverPrompt
from superpilot.examples.ed_tech.solution_validator import SolutionValidatorPrompt
from superpilot.framework.tools.latex import latex_to_text
from superpilot.tests.test_env_simple import get_env
from superpilot.core.configuration.config import get_config
from superpilot.core.ability.super import SuperAbilityRegistry
from superpilot.examples.ed_tech.ag_question_solver_ability import (
    AGQuestionSolverAbility
)

from superpilot.core.pilot.task.super import SuperTaskPilot
from superpilot.core.pilot.chain.simple import SimpleChain
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    AnthropicModelName,
    OpenAIModelName,
)
from superpilot.core.planning.settings import (
    LanguageModelConfiguration,
    LanguageModelClassification,
)
from superpilot.core.pilot.settings import (
    PilotConfiguration,
    ExecutionAlgo, ExecutionNature
)
from superpilot.examples.email.transformer_prompt import TransformerPrompt
from superpilot.examples.email.base_ability import DefaultAbility,ScheduleMeetingAbility,CreateTaskAbility,CreateReminderAbility,SummarizeEmailAbility,ExtractEntitiesAbility

from superpilot.examples.email.file_processing import eml_to_text
from superpilot.examples.email.agents_search import AgentSearchSystem





class SuperEmail(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()
    
    config = get_config()
    env = get_env({})
    ALLOWED_ABILITY = {
        ScheduleMeetingAbility.name(): ScheduleMeetingAbility.default_configuration,
        CreateTaskAbility.name(): CreateTaskAbility.default_configuration,
        CreateReminderAbility.name(): CreateReminderAbility.default_configuration,
        SummarizeEmailAbility.name(): SummarizeEmailAbility.default_configuration,
        ExtractEntitiesAbility.name(): ExtractEntitiesAbility.default_configuration
        
    }

    def __init__(self, thread_id: str,email:str, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        super_ability_registry = SuperAbilityRegistry.factory(
            self.env, self.ALLOWED_ABILITY
        )

        self.thread_id = thread_id
        self.email = email
        asyncio.run(self.init())

    async def init(self):
        environment = get_env({})
        state = PickleState(thread_id=self.thread_id, workspace=environment.workspace)
        self.context = await state.load()

        call_back_manager = STDInOutCallbackManager(
            callbacks=[SimpleCallbackHandler(thread_id=self.thread_id)],
            thread_id=self.thread_id
        )
        
        self.chain = SuperChain(
            state=state,
            callback=call_back_manager,
            thread_id=self.thread_id,
            context=self.context,
        )
        transform_pilot = SimpleTaskPilot.create(
            prompt_config=TransformerPrompt.default_configuration,
            model_providers=self.model_providers,
            smart_model_name=OpenAIModelName.GPT4_TURBO,
            fast_model_name=OpenAIModelName.GPT3,
            pilot_config=PilotConfiguration(
                name="transform_pilot",
                role=(
                    "An AI Pilot converting the text into given json format"
                ),
                goals=[
                    "Transform the text into given json format",
                ],
                cycle_count=0,
                max_task_cycle_count=3,
                creation_time="",
                execution_nature=ExecutionNature.AUTO,
            )
        )

        email_pilot = SuperPilot.create(
            context=self.context,
            model_providers=self.model_providers,
            state=state,
            pilot_config=PilotConfiguration(
                name="email_pilot",
                role=(
                    "An AI Pilot performing email tasks"
                ),
                goals=[
                    "Perform email tasks",
                    "Schedule meetings",
                    "Create tasks",
                    "Create reminders",
                    "Summarize email content",
                    "Extract entities like dates, names, and numbers from email content",
                ],
                cycle_count=0,
                max_task_cycle_count=3,
                creation_time="",
                execution_nature=ExecutionNature.AUTO,
            ),
            callback=call_back_manager,
            thread_id=self.thread_id,
            abilities=[ScheduleMeetingAbility,CreateTaskAbility,CreateReminderAbility,SummarizeEmailAbility,ExtractEntitiesAbility]
            
        )

        observer_pilot = SimpleTaskPilot.create(
            prompt_config=ObserverPrompt.default_configuration,
            smart_model_name=OpenAIModelName.GPT4,
            fast_model_name=OpenAIModelName.GPT3,
            pilot_config=PilotConfiguration(
                name="observer_pilot",
                role=(
                    "An AI Pilot observing the conversation and selecting the next pilot to play."
                ),
                goals=[
                    "Observe the conversation and determine if task is completed or not.",
                    "Select the next pilot to play.",
                ],
                cycle_count=0,
                max_task_cycle_count=3,
                creation_time="",
                execution_nature=ExecutionNature.AUTO,
            ),
            callback = call_back_manager,
            thread_id=self.thread_id,
        )

        #self.chain.add_pilot(transform_pilot)
        #self.chain.add_pilot(email_pilot)
        self.chain.add_handler(email_pilot)
        self.chain.add_observer(observer_pilot)

    

    PROMPT_TEMPLATE = """
                -------------
                Question: {question}
                -------------
                Solution: {solution}
                """

    


    def process_email(self):
        print(f"Processing email: {self.email}")
        output_folder = "attachments"
        eml_file_path = self.email
        
        content_items = []
    
    # Parse the .eml file
        with open(eml_file_path, 'rb') as eml_file:
            msg = BytesParser(policy=policy.default).parse(eml_file)
        
        # Loop through the email parts to find attachments
        for part in msg.iter_attachments():
            filename = part.get_filename()
            if filename:
                # Save the attachment temporarily to create a FileContentItem
                attachment_path = Path(f"temp_attachments/{filename}")
                attachment_path.parent.mkdir(exist_ok=True)
                with open(attachment_path, 'wb') as file:
                    file.write(part.get_payload(decode=True))
                
                # Create a FileContentItem
                content_item = FileContentItem(file_path=attachment_path)
                content_items.append(content_item)
    
    
        with open(self.email, 'rb') as eml_file:       
            text=eml_to_text(eml_file)
        message=Message.create(text, event=Event.USER_INPUT)
        message.attachments=content_items
        self.context.add_message(message)
        return(message)
    

    def tasks_from_email(self):
        message=self.process_email()
        print("Creating tasks")

        client = OpenAI()

        completion = client.chat.completions.create(
            model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a task extraction assistant."},
            {"role": "user", "content": f"Extract five major task objectives from the following email:\n{message.message}"},
        ]
        )
    
        response = completion.choices[0].message.content
        tasks_list = [re.sub(r'^\d+\.\s*', '', task.strip()) for task in response.split('\n') if task.strip()]

        return tasks_list

        


    

        


    
    
    def create_agents(self):
        print("Creating agents")

        agents=[]

        tasks_list=self.tasks_from_email()
        for task in tasks_list:
            agent = AgentSearchSystem(api_url='http://qa-search-service.co/api/v1/search/query/agents/')

            agents.append(agent.run(query=task))

            

        
        
    
    
    def auto_transformer(self, data, response, context):
        print("Auto solver transformer", data, response)
        # response = {
        #     "question": data,
        #     "solution": response.format_numbered(),
        # }
        # task = self.PROMPT_TEMPLATE.format(**response)
        return response, context

    async def execute(self, task: str):
        await self.init()
        await self.chain.execute(task)

    async def run(self, query):
        await self.execute(query)

    def format_numbered(self, items) -> str:
        if not items:
            return ""
        return "\n".join([f"{i}) {c}" for i, c in enumerate(items, 1)])

    async def run_list(self, _list: List[str]):
        final_res = []
        try:
            for index, path in enumerate(_list):
                response = await self.run(path)
                final_res.append({"path": path, **response})
                print(f"Query {response.get('question')}", "\n\n")
                print(f"Solution {response.get('solution')}", "\n\n")
                print(f"Query {index} finished", "\n\n")
        except Exception as e:
            print(e)
        return final_res
    


if __name__ == "__main__":
    # state = State()
    thread_id = "thread1234567891011121314151617"
    email = r"C:\Users\hp\Downloads\sample.eml"
    email = SuperEmail(thread_id=thread_id,email=email)    