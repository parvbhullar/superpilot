import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from superpilot.core.configuration import get_config
from superpilot.core.context.schema import Context
from superpilot.core.pilot.chain.strategy.observation_strategy import ObserverPrompt
from superpilot.core.pilot.chain.super import SuperChain
from superpilot.core.pilot.settings import PilotConfiguration, ExecutionAlgo, ExecutionNature
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.pilot.task.super import SuperTaskPilot
from superpilot.core.resource.model_providers import OpenAIModelName
from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.examples.rag.abilities.observer_ability import ObserverAbility
from superpilot.examples.rag.abilities.qdrant_ability import QdrantAbility
from superpilot.examples.rag.abilities.reco_ability import RecoAbility
from superpilot.tests.test_env_simple import get_env

import asyncio
import time
from abc import abstractmethod
from superpilot.core.callback.handler.simple import SimpleCallbackHandler
from superpilot.core.callback.manager.simple import SimpleCallbackManager
from superpilot.core.callback.manager.std_io import STDInOutCallbackManager


class DataGPTExecutor:
    model_providers = ModelProviderFactory.load_providers()

    context = Context()
    config = get_config()
    chain = SuperChain()
    env = get_env({})

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.reco_api_pilot = SuperTaskPilot.create(
            model_providers=self.model_providers,
            smart_model_name=OpenAIModelName.GPT4_TURBO,
            fast_model_name=OpenAIModelName.GPT3_16K,
            pilot_config=PilotConfiguration(
                name="Reco_Api_Pilot",
                role=(
                    f"This pilot is responsible for calling the reco api and returning the result to the user."
                ),
                goals=[
                    f"To call appropriate reconcile ability and returned data from that ability"
                ],
                cycle_count=0,
                max_task_cycle_count=3,
                creation_time="",
                execution_nature=ExecutionNature.AUTO,
            ),
            execution_nature=ExecutionNature.SEQUENTIAL,
            abilities=[RecoAbility],
        )
        
        self.context_builder_pilot = SuperTaskPilot.create(
            model_providers=self.model_providers,
            smart_model_name=OpenAIModelName.GPT4_TURBO,
            fast_model_name=OpenAIModelName.GPT3_16K,
            pilot_config=PilotConfiguration(
                name="RAG_Context_Builder_Pilot",
                role=(
                    f"This pilot is responsible for calling the qdrant api and returning the result to the user."
                ),
                goals=[
                    "To call appropriate qdrant ability and returned data from that ability",
                ],
                cycle_count=0,
                max_task_cycle_count=3,
                creation_time="",
                execution_nature=ExecutionNature.AUTO,
            ),
            execution_nature=ExecutionNature.SEQUENTIAL,
            abilities=[QdrantAbility],
            )

        self.Observer_Pilot = SimpleTaskPilot.create(
            prompt_config=ObserverPrompt.default_configuration,
            smart_model_name=OpenAIModelName.GPT4_TURBO,
            fast_model_name=OpenAIModelName.GPT3,
            # smart_model_temp=0,
            # fast_model_temp=0,
            pilot_config=PilotConfiguration(
                name="observer_pilot",
                role=(
                    "An AI Pilot observing the user context, conversation and selecting the next pilot to play."
                ),
                goals=[
                    "Observe the conversation and determine if task is completed or not.",
                    "Select the next pilot to play.",
                ],
                cycle_count=0,
                max_task_cycle_count=3,
                creation_time="",
                execution_nature=ExecutionNature.AUTO,
            )
        )

        self.chain.add_handler(self.reco_api_pilot)
        self.chain.add_handler(self.context_builder_pilot)
        self.chain.add_observer(self.Observer_Pilot)

    def sample_chain_function(self, data, response, context):
        # print("Sample chain Task: ", data)
        pass

    def format_transformer(self, data, response, context):
        # print("format_transformer", response)
        task = response.dict()
        context = response
        # print(task)
        return task, context

    PROMPT_TEMPLATE = """ You are a Observer Engine which observes data and execute given ability depending on user input data and 
                its context, Decides nest ability next ability. """

    async def execute(self, task: str, **kwargs):
        # task = {}
        self.context.add("")

        # task = Task.factory(task, **kwargs)
        # response = await self.api_pilot.execute(task, self.context, **kwargs)
        response, context = await self.chain.execute(task, self.context, **kwargs)
        print('\nresponse----->',response)
        last_newline_index = str(response).rfind('\n\n')  # Finding the index of the last newline character
        data_after_last_newline = str(response)[last_newline_index+1:]
        print('\ncontext ----->',context)
        # print(response)
        return str(data_after_last_newline)

    async def run(self, context):
        response = await self.execute(context, user="user")
        # print(response)
        return response


if __name__ == "__main__":
    # state = State()
    thread_id = "thread1"
    data_gpt = DataGPTExecutor()
    # print(asyncio.run(calc.run("add 2 and 3")))
    print(asyncio.run(data_gpt.run("for RECO GSTR2A for buyer gstin 09AAACU6815C1ZH,financial year For 2023-24 using reco api and give total tax")))
