from typing import List
from superpilot.core.context.schema import Context
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.resource.model_providers.factory import ModelProviderFactory, ModelConfigFactory
from superpilot.examples.ed_tech.teacher_guide.topics_prompt import TopicsPrompt
from superpilot.examples.ed_tech.teacher_guide.topics_prompt_hn import TopicsPromptHN
from superpilot.examples.executor.base import BaseExecutor
from superpilot.examples.ed_tech.question_solver import QuestionSolverPrompt
from superpilot.examples.ed_tech.solution_validator import SolutionValidatorPrompt
from superpilot.examples.ed_tech.describe_image_question import DescribeQFigurePrompt
from superpilot.framework.tools.latex import latex_to_text
from superpilot.tests.test_env_simple import get_env
from superpilot.core.configuration.config import get_config
from superpilot.core.ability.super import SuperAbilityRegistry
from superpilot.examples.ed_tech.ag_question_solver_ability import (
    AGQuestionSolverAbility,
)
from superpilot.core.pilot.chain.simple import SimpleChain
from superpilot.examples.pilots.tasks.super import SuperTaskPilot
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    AnthropicModelName,
    OpenAIModelName,
)
from superpilot.core.planning.settings import (
    LanguageModelConfiguration,
    LanguageModelClassification,
)


class GuideExecutor(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()
    context = Context()
    config = get_config()
    chain = SimpleChain()
    env = get_env({})
    ALLOWED_ABILITY = {
        # SearchAndSummarizeAbility.name(): SearchAndSummarizeAbility.default_configuration,
        # TextSummarizeAbility.name(): TextSummarizeAbility.default_configuration,
        AGQuestionSolverAbility.name(): AGQuestionSolverAbility.default_configuration,
    }

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        super_ability_registry = SuperAbilityRegistry.factory(
            self.env, self.ALLOWED_ABILITY
        )
        self.super_prompt = QuestionSolverPrompt.factory()

        vision_pilot = SimpleTaskPilot.create(
                DescribeQFigurePrompt.default_configuration,
                model_providers=self.model_providers,
                smart_model_name=OpenAIModelName.GPT4_VISION,
                fast_model_name=OpenAIModelName.GPT3,
            )
        topics_pilot = SimpleTaskPilot.create(
                # TopicsPrompt.default_configuration,
                TopicsPromptHN.default_configuration,
                model_providers=self.model_providers,
                smart_model_name=OpenAIModelName.GPT4_TURBO,
                fast_model_name=OpenAIModelName.GPT3,
            )
        # format_pilot = SimpleTaskPilot.create(
        #         SolutionValidatorPrompt.default_configuration,
        #         model_providers=self.model_providers,
        #         smart_model_name=OpenAIModelName.GPT4_TURBO,
        #         fast_model_name=OpenAIModelName.GPT3,
        #     )
        # auto_solver_pilot = SuperTaskPilot(super_ability_registry, self.model_providers)
        # print("VISION", vision_pilot)

        # Initialize and add pilots to the chain here, for example:
        # self.chain.add_handler(vision_pilot, self.vision_transformer)
        # self.chain.add_handler(auto_solver_pilot, self.vision_transformer)
        self.chain.add_handler(topics_pilot, self.solver_transformer)
        # self.chain.add_handler(format_pilot, self.format_transformer)

    def auto_solver_transformer(self, data, response, context):
        # print("Auto solver transformer", data, response)
        response = {
            "question": data,
            "solution": response.format_numbered(),
        }
        task = self.PROMPT_TEMPLATE.format(**response)
        return task, context

    def vision_transformer(self, data, response, context):
        response = {
            "question": response.get("content", data),
            "solution": "",
        }
        task = self.PROMPT_TEMPLATE.format(**response)
        return task, context

    def solver_transformer(self, data, response, context):
        print("Solver transformer", data, response)
        return response, context

    def format_transformer(self, data, response, context):
        # print("Task: ", data)
        # print("Response: ", response)
        # print("Context: ", context)
        response = {
            "question": data,
            "solution": response.get("content", ""),
        }
        # task = self.PROMPT_TEMPLATE.format(**response)
        return response, context

    PROMPT_TEMPLATE = """
            -------------
            Question: {question}
            -------------
            Solution: {solution}
            """

    async def execute(self, task: str, chapter: str, **kwargs):
        self.context.add(chapter)
        response, context = await self.chain.execute(task, self.context, **kwargs)

        # print("Task: ", response)
        # print("Context: ", context)
        # Execute for Sequential nature
        # response = {}

        # r = await pilot.execute(task, self.context, **kwargs)
        # if isinstance(r, Context):
        #     self.context.extend(r)
        #     response.update(r.dict())
        # else:
        #     response.update(r)

        return response.get("content")

    async def run(self, chapter: str):
        query = "Generate guide for given chapter"
        response = await self.execute(query, chapter)
        # print(response)
        return response

    def format_numbered(self, items) -> str:
        if not items:
            return ""
        return "\n".join([f"{i}) {c}" for i, c in enumerate(items, 1)])

    async def run_list(self, path_list: List[str]):
        final_res = []
        try:
            for index, path in enumerate(path_list):
                response = await self.run(path)
                final_res.append({"path": path, **response})
                print(f"Query {response.get('question')}", "\n\n")
                print(f"Solution {response.get('solution')}", "\n\n")
                print(f"Query {index} finished", "\n\n")
        except Exception as e:
            print(e)
        return final_res

