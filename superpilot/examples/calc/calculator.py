import os
import sys
import asyncio
import time
from abc import abstractmethod

from superpilot.core.callback.handler.simple import SimpleCallbackHandler
from superpilot.core.callback.manager.simple import SimpleCallbackManager
from superpilot.core.callback.manager.std_io import STDInOutCallbackManager

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from superpilot.core.state.base import State
from superpilot.core.state.pickle import PickleState


from superpilot.core.pilot.chain.strategy.observation_strategy import ObserverPrompt
from superpilot.core.pilot.chain.super import SuperChain
from typing import List
from superpilot.core.context.schema import Context
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
    ExecutionAlgo
)
from superpilot.examples.calc.transformer_prompt import TransformerPrompt
from superpilot.examples.calc.base_ability import AddAbility, MultiplyAbility, SubtractAbility, DivisionAbility, \
    RootAbility, DefaultAbility


class Calculator(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()
    context = Context()
    config = get_config()
    env = get_env({})
    ALLOWED_ABILITY = {
        AddAbility.name(): AddAbility.default_configuration,
        MultiplyAbility.name(): MultiplyAbility.default_configuration,
        SubtractAbility.name(): SubtractAbility.default_configuration,
        DivisionAbility.name(): DivisionAbility.default_configuration,
        RootAbility.name(): RootAbility.default_configuration,
    }

    def __init__(self, thread_id: str, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        super_ability_registry = SuperAbilityRegistry.factory(
            self.env, self.ALLOWED_ABILITY
        )

        environment = get_env({})
        state = PickleState(thread_id=thread_id, workspace=environment.workspace)

        self.chain = SuperChain(
            state=state,
            callback=STDInOutCallbackManager(
                callbacks=[SimpleCallbackHandler()]
            )
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
                execution_algo=ExecutionAlgo.PLAN_AND_EXECUTE,
            )
        )
        calculator = SuperTaskPilot.create(
            model_providers=self.model_providers,
            pilot_config=PilotConfiguration(
                name="calculator",
                role=(
                    "An AI calculator Pilot"
                ),
                goals=[
                    "Perform basic arithmetic operations"
                    "Perform addition, subtraction, multiplication, division and root",
                ],
                cycle_count=0,
                max_task_cycle_count=3,
                creation_time="",
                execution_algo=ExecutionAlgo.PLAN_AND_EXECUTE,
            ),
            callback=STDInOutCallbackManager(
                callbacks=[SimpleCallbackHandler()]
            ),
            abilities=[AddAbility, MultiplyAbility, SubtractAbility, DivisionAbility, RootAbility, DefaultAbility],
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
                execution_algo=ExecutionAlgo.PLAN_AND_EXECUTE,
            )
        )

        # transform_pilot.execute("Choose the pilot based on given task.", )

        # print("VISION", vision_pilot)

        # Initialize and add pilots to the chain here, for example:
        self.chain.add_handler(transform_pilot, self.auto_transformer)
        self.chain.add_handler(calculator)
        self.chain.add_observer(observer_pilot)

    PROMPT_TEMPLATE = """
                -------------
                Question: {question}
                -------------
                Solution: {solution}
                """


    def auto_transformer(self, data, response, context):
        print("Auto solver transformer", data, response)
        # response = {
        #     "question": data,
        #     "solution": response.format_numbered(),
        # }
        # task = self.PROMPT_TEMPLATE.format(**response)
        return response, context

    async def execute(self, task: str):
        response, context = await self.chain.execute(task, self.context)
        return response

    async def run(self, query):
        response = await self.execute(query)
        return response

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
    thread_id = "thread1"
    calc = Calculator(thread_id=thread_id)
    # print(asyncio.run(calc.run("add 2 and 3")))
    # print(
    #     asyncio.run(calc.run("transform data from text and multiply 2 and 3 and then sum with 6 and then subtract 2 "
    #                          "and then divide by 2 and plot the graph using data from text")))
    # print(asyncio.run(calc.run("Multiply few given numbers with 3")))
    print(asyncio.run(calc.run("add 2 and 3")))
    # print(asyncio.run(calc.run("Please find the doc number 1 and date is 12-2-2021")))
    # print('='*100)
    # calc2 = Calculator(state=state)
    # print(asyncio.run(calc2.run("User Answer")))
