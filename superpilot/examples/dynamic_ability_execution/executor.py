import asyncio
import logging
import os
import sys

from superpilot.core.ability import Ability
from superpilot.core.planning import SimplePlanner, LanguageModelClassification
from superpilot.core.planning.settings import PlannerSettings, PlannerConfiguration, LanguageModelConfiguration
from superpilot.core.planning.strategies import NextAbility, NextAbilityConfiguration
from superpilot.core.planning.strategies.planning_strategy import PlanningStrategy
from superpilot.core.resource.model_providers import OpenAIModelName, ModelProviderName

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from superpilot.core.pilot import SuperPilot

from superpilot.core.callback.handler.simple import SimpleCallbackHandler
from superpilot.core.callback.manager.std_io import STDInOutCallbackManager

from superpilot.core.state.base import State

from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.examples.executor.base import BaseExecutor
from superpilot.tests.test_env_simple import get_env
from superpilot.core.configuration.config import get_config, Config

from superpilot.core.pilot.settings import (
    PilotConfiguration,
    ExecutionNature
)

model_mapping = {
    ModelProviderName.OPENAI: {
        'ADA': OpenAIModelName.ADA,
        'GPT3': OpenAIModelName.GPT3,
        'GPT3_16K': OpenAIModelName.GPT3_16K,
        'GPT4': OpenAIModelName.GPT4,
        'GPT4_32K': OpenAIModelName.GPT4_32K,
        'GPT4_TURBO': OpenAIModelName.GPT4_TURBO,
        'GPT4_VISION': OpenAIModelName.GPT4_VISION,
        'GPT4_32K_NEW': OpenAIModelName.GPT4_32K_NEW,
        'GPT3_FINETUNE_MODEL': OpenAIModelName.GPT3_FINETUNE_MODEL,
        'GPT4_O': OpenAIModelName.GPT4_O
    }
}

model_provider_mapping = {'OPEN_AI': ModelProviderName.OPENAI}


class SuperDynamicPilot(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()

    config = get_config()
    env = get_env({})

    def __init__(self, thread_id: str, json_config, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.thread_id = thread_id
        self.json_data = json_config

    async def init(self):
        environment = get_env({})
        state = State(thread_id=self.thread_id, workspace=environment.workspace)
        self.context = await state.load()

        call_back_manager = STDInOutCallbackManager(
            callbacks=[SimpleCallbackHandler(thread_id=self.thread_id)],
            thread_id=self.thread_id
        )

        abilities = [create_class_from_json(ability_conf) for ability_conf in self.json_data['abilities']]

        model_provider = model_provider_mapping.get(self.json_data['model_config']['provider_name'],
                                                    ModelProviderName.OPENAI)
        model_name = model_mapping.get(model_provider).get(self.json_data['model_config']['model_name'], 'GPT4')
        self.dynamic_pilot = SuperPilot.create(
            context=self.context,
            model_providers=self.model_providers,
            planner=SimplePlanner(
                context=self.context,
                settings=PlannerSettings(
                    name="planner",
                    description="Manages the pilot's planning and goal-setting by constructing language model prompts.",
                    configuration=PlannerConfiguration(
                        models={
                            LanguageModelClassification.FAST_MODEL: LanguageModelConfiguration(
                                model_name=OpenAIModelName.GPT3,
                                provider_name=ModelProviderName.OPENAI,
                                temperature=0.9,
                            ),
                            LanguageModelClassification.SMART_MODEL: LanguageModelConfiguration(
                                model_name=model_name,
                                provider_name=model_provider,
                                temperature=self.json_data['model_config'].get('temperature', 0.9),
                            ),
                        },
                        planning_strategy=PlanningStrategy.default_configuration,
                        execution_strategy=NextAbilityConfiguration(
                            model_classification=LanguageModelClassification.SMART_MODEL,
                            system_prompt_template=NextAbility.DEFAULT_SYSTEM_PROMPT_TEMPLATE,
                            system_info=NextAbility.DEFAULT_SYSTEM_INFO,
                            user_prompt_template=f"{NextAbility.DEFAULT_USER_PROMPT_TEMPLATE}\n"
                                                 f"{self.json_data['model_config'].get('user_prompt', '')}",
                            additional_ability_arguments=NextAbility.DEFAULT_ADDITIONAL_ABILITY_ARGUMENTS,
                        ),
                        reflection_strategy=PlanningStrategy.default_configuration,
                    ),
                ),
                workspace=environment.get("workspace"),
                logger=environment.get("logger"),
                callback=call_back_manager,
                model_providers=self.model_providers,
                state=state
            ),
            state=state,
            pilot_config=PilotConfiguration(
                name="dynamic_pilot",
                role=(
                    "An AI Dynamic Pilot"
                ),
                goals=[
                    "Run user defiend functions",
                ],
                cycle_count=0,
                max_task_cycle_count=3,
                creation_time="",
                execution_nature=ExecutionNature.SEQUENTIAL,
            ),
            callback=call_back_manager,
            thread_id=self.thread_id,
            abilities=abilities
        )

    async def execute(self, task: str):
        await self.init()
        return await self.dynamic_pilot.execute(task)

    async def run(self, query):
        return await self.execute(query)


def create_class_from_json(ability_config):
    # Define a dictionary to store method references
    methods = {}

    # Pick methods from JSON data
    for method_name in ["__call__"]:
        method_data = ability_config["methods"].get(method_name, None)

        # Create a function dynamically
        def make_func(data):
            async def func(*args, ability_args, **kwargs):
                if data:
                    loc = {**locals(), **ability_args}
                    exec(data["body"], globals(), loc)
                    # exec(data["body"], globals(), locals())
                    result = loc['result']
                    print(result)
                    return result
                else:
                    return ability_args

            return func

        func = make_func(method_data)
        func.__name__ = method_name
        methods[method_name] = func

    for method_name in ["arguments", "name", "description"]:
        method_data = ability_config["methods"][method_name]
        print(method_name, method_data)

        # Create a function dynamically
        def make_func(data):
            def func(*args, **kwargs):
                return data

            return func

        func = make_func(method_data)
        func.__name__ = method_name
        methods[method_name] = func

    # Define __init__ method
    def __init__(self, environment):
        self._logger: logging.Logger = environment.get("logger")
        # self._configuration = configuration
        self._env_config: Config = environment.get("env_config")

    # Create the class dynamically using type()
    cls = type(
        ability_config["class_name"],
        (Ability,),
        {
            **{attr: val for attr, val in ability_config["attributes"].items()},
            **methods,
            "__init__": __init__
        }
    )

    return cls


async def dynamic_run_llm(query, json_data):
    thread_id = "thread1234567891011121314151617"
    calc = SuperDynamicPilot(thread_id=thread_id, json_config=json_data)
    return await calc.run(query)


if __name__ == "__main__":
#     json_data = {
#         "model_config": {
#             "model_name": "GPT4",
#             "provider_name": "OPEN_AI",
#             "temperature": 0.9,
#             "user_prompt": "convert from hindi to english"
#         },
#         "abilities": [
#             {
#                 "class_name": "DynamicAbility",
#                 "attributes": {
#                     "default_configuration": None
#                 },
#                 "methods": {
#                     "__call__": {
#                         "body": '''
# res = ability_args["num1"] + ability_args["num2"]
# if res >= 0:
#     ans = "greater"
# else:
#     ans = "less"
# print(ans)
# result = ans
# '''
#                     },
#                     "arguments": {
#                         "num1": {"type": "number", "description": "The first number."},
#                         "num2": {"type": "number", "description": "The second number."},
#                     },
#                     "name": "add",
#                     "description": "Block to add two numbers"
#                 }
#             },
#             {
#                 "class_name": "DynamicAbility",
#                 "attributes": {
#                     "default_configuration": None
#                 },
#                 "methods": {
#                     "__call__": {
#                         "body": '''
# res = ability_args["num1"] - ability_args["num2"]
# if res >= 0:
#     ans = "greater"
# else:
#     ans = "less"
# print(ans)
# print(res)
# result = ans
# '''
#                     },
#                     "arguments": {
#                         "num1": {"type": "number", "description": "The first number."},
#                         "num2": {"type": "number", "description": "The second number."},
#                     },
#                     "name": "subtract",
#                     "description": "Block to add two numbers"
#                 }
#             },
#         ]
#     }

    # # state = State()
    # thread_id = "thread1234567891011121314151617"
    # calc = SuperDynamicPilot(thread_id=thread_id, json_config=json_data)
    # print(asyncio.run(calc.run("What is 3 plus 2 minus 5")))
    # ans = asyncio.run(dynamic_run_llm("What is 3 plus 2 minus 5", json_data))
    # print(ans, "MY ans")
    translation = asyncio.run(
        dynamic_run_llm(
            "How Are You?",
            {
                "model_config": {
                    "model_name": "GPT4",
                    "provider_name": "OPEN_AI",
                    "temperature": 0.9,
                    "user_prompt": "convert from english to hindi"
                },
                "abilities": [
                    {
                        'class_name': 'DynamicAbility',
                        'attributes': {'default_configuration': None},
                        'methods': {
                            # '__call__': {'body': 'print(original_string)\nresult = ability_args'},
                            'arguments': {
                                'original_string': {'type': 'string', 'description': 'source string'},
                                'translated_string': {'type': 'string', 'description': 'translated result string '}
                            },
                            'name': 'translate',
                            'description': "convert from english to hindi"
                        }
                    }
                ]
            }
        )
    )

    print('we got', translation)
