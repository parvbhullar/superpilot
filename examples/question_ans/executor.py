import asyncio

import pandas as pd

from superpilot.core.configuration.config import get_config
from superpilot.core.context.schema import Context
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.resource.model_providers import (
    OpenAIModelName,
)
from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.examples.executor.base import BaseExecutor
from superpilot.examples.question_ans.prompt import QuestionAnswerAnalysisPrompt
from superpilot.framework.tools.latex import latex_to_text
from superpilot.tests.test_env_simple import get_env


class QuestionExecutor(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()
    context = Context()
    config = get_config()
    env = get_env({})

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.analysis_pilot = SimpleTaskPilot.create(
            QuestionAnswerAnalysisPrompt.default_configuration,
            model_providers=self.model_providers,
            smart_model_name=OpenAIModelName.GPT4,
            fast_model_name=OpenAIModelName.GPT3,
        )

    PROMPT_TEMPLATE = """
    ---------------------
    Question: {question}
    ----------------------
    Answer: {solution}
    ----------------------
    SOP excel sheet: {sop}
    _______________________
    Task: Perform a question answer analysis based on the SOP
    """

    async def process_row(self, row):
        question = row['Question Body']
        solution = row['Answer HTML']
        sop_file = '/Users/shivam/Downloads/SOP-Civil Engg..xlsx'
        df = pd.read_excel(sop_file)
        sop = df.to_string(index=False)
        sop = latex_to_text(sop)
        prompt = self.PROMPT_TEMPLATE.format(question=question, solution=solution, sop=sop)
        response = await self.analysis_pilot.execute(prompt)
        return response

    async def execute(self, **kwargs):
        input_file_path = '/Users/shivam/Documents/sample_question.xlsx'
        df = pd.read_excel(input_file_path)
        for index, row in df.iterrows():
            response = await self.process_row(row)
            for col_name, col_value in response.content.items():
                df.at[index, col_name] = col_value

        df.to_excel('output.xlsx', index=False)

    async def run(self, query):
        pass


if __name__ == '__main__':
    executor = QuestionExecutor()
    asyncio.run(executor.execute())
