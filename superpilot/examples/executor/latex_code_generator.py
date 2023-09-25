from typing import Dict, List
from superpilot.core.context.schema import Context
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.examples.executor.base import BaseExecutor
from superpilot.examples.prompt_generator.latex_code_gen import (
    LatexCodeGenPrompt,
)
from superpilot.framework.tools.latex import latex_to_text
from superpilot.core.planning.strategies.utils import json_loads


class LatexCodeGenExecutor(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()
    context = Context()

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.super_prompt = LatexCodeGenPrompt.factory()
        self.pilot = SimpleTaskPilot.factory(
            prompt_strategy=self.super_prompt.get_config(),
            model_providers=self.model_providers,
        )

    async def run(self, query):
        response = await self.pilot.execute(query)
        response.content = json_loads(response.content.get("content", "{}"))
        options = self.format_numbered(response.content.get("options", []))
        response.content["question"] = latex_to_text(response.content.get("question", ""))
        response.content["question"] += f"\n{options}\n"
        response.content["options"] = options
        return response

    def format_numbered(self, items) -> str:
        return "\n".join([f"{i}) {c}" for i, c in enumerate(items, 1)])

    async def run_list(self, query_list: List[Dict]):
        final_res = []
        for index, query in enumerate(query_list):
            response = await self.run(query.get("Original Keyword"))
            final_res.append({**query, **response.content})
            print(f"Query {index} finished", "\n\n")
        return final_res
