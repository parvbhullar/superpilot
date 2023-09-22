from typing import Dict, List
from superpilot.core.context.schema import Context
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.examples.executor.base import BaseExecutor
from superpilot.examples.prompt_generator.question_correct import (
    QuestionIdentifierPrompt,
)


class QuestionIdentifierPromptExecutor(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()
    context = Context()

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.super_prompt = QuestionIdentifierPrompt.factory()
        self.pilot = SimpleTaskPilot.factory(
            prompt_strategy=self.super_prompt.get_config(),
            model_providers=self.model_providers,
        )

    async def run(self, query):
        response = await self.pilot.execute(query)
        return response

    async def run_list(self, query_list: List[Dict]):
        final_res = []
        for index, query in enumerate(query_list):
            response = await self.run(query.get("Original keyword"))
            final_res.append({**response.content, **query})
            print(f"Query {index} finished", "\n\n")
        return final_res
