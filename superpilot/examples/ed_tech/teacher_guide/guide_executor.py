from typing import List
from superpilot.core.context.schema import Context
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.resource.model_providers.factory import ModelProviderFactory

from superpilot.examples.ed_tech.teacher_guide.topics_prompt_hn import TopicsPromptHN
from superpilot.examples.ed_tech.teacher_guide.summary_prompt_hn import (
    TopicSummaryPromptHN,
)
from superpilot.examples.executor.base import BaseExecutor
from superpilot.tests.test_env_simple import get_env
from superpilot.core.configuration.config import get_config
from superpilot.core.pilot.chain.simple import SimpleChain
from superpilot.core.resource.model_providers import OpenAIModelName


class GuideExecutor(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()
    context = Context()
    config = get_config()
    chain = SimpleChain()
    env = get_env({})

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        topics_pilot = SimpleTaskPilot.create(
            TopicsPromptHN.default_configuration,
            model_providers=self.model_providers,
            smart_model_name=OpenAIModelName.GPT4_TURBO,
            fast_model_name=OpenAIModelName.GPT3,
        )
        summary_pilot = SimpleTaskPilot.create(
            TopicSummaryPromptHN.default_configuration,
            model_providers=self.model_providers,
            smart_model_name=OpenAIModelName.GPT4_TURBO,
            fast_model_name=OpenAIModelName.GPT3,
        )
        self.chain.add_handler(topics_pilot, self.content_transformer)
        self.chain.add_handler(summary_pilot, self.content_transformer)

    def content_transformer(self, data, response, context):
        self.final_content += response.get("content")
        return response.get("content"), context

    def solver_transformer(self, data, response, context):
        return response.get("content"), context

    async def execute(self, task: str, chapter: str, **kwargs):
        self.context.add(chapter)
        self.final_content = ""
        await self.chain.execute(task, self.context, **kwargs)
        return self.final_content

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
