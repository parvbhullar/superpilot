# from superpilot.core.ability.super import SuperAbilityRegistry
from typing import Dict, List
from superpilot.core.configuration.config import get_config

from superpilot.core.context.schema import Context

# from superpilot.core.planning.schema import Task
from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.examples.abilities.question_extractor import QuestionExtractor
from superpilot.examples.executor.base import BaseExecutor
from superpilot.examples.executor.latex_code_generator import LatexCodeGenExecutor

# from superpilot.examples.pilots.tasks.super import SuperTaskPilot
from superpilot.tests.test_env_simple import get_env

ALLOWED_ABILITY = {QuestionExtractor.name(): QuestionExtractor.default_configuration}


class QuestionExtractorExecutor(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()
    config = get_config()
    env = get_env({})
    context = Context()

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.ability = QuestionExtractor(environment=self.env)

    async def run(self, query):
        # context = await self.ability(query)
        # if not context:
        #     print("No Data Found")
        #     context = query
        context = query
        latex_convertor = LatexCodeGenExecutor()
        print("\n", "*" * 32, "Running LatexCodeGenExecutor", "*" * 32, "\n\n")
        content = await latex_convertor.run(str(context))
        return content

    async def run_list(self, query_list: List[Dict]):
        final_res = []
        error_res = []
        for index, query in enumerate(query_list):
            try:
                response = await self.run(query.get("Original Keyword"))
                final_res.append(
                    {**query, **response.content, "total_cost($)": response.total_cost}
                )
                print(f"Query {index} finished", "\n\n")
            except Exception as e:
                try:
                    print("Trying to run again")
                    response = await self.run(query.get("Original Keyword"))
                    final_res.append(
                        {
                            **query,
                            **response.content,
                            "total_cost($)": response.total_cost,
                        }
                    )
                    print(f"Query {index} finished", "\n\n")
                except Exception as e:
                    print(e, "Query Failed")
                    error_res.append(query)
        return final_res, error_res
