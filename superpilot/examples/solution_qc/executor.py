import pandas as pd

from superpilot.core.configuration.config import get_config
from superpilot.core.context.schema import Context
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.resource.model_providers import (
    OpenAIModelName,
)
from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.examples.executor.base import BaseExecutor
from superpilot.examples.solution_qc.constants import SOP_FILE_MAP
from superpilot.examples.solution_qc.prompt import QuestionAnswerAnalysisPrompt
from superpilot.examples.solution_qc.utils import EmptyObject
from superpilot.framework.tools.latex import latex_to_text
from superpilot.tests.test_env_simple import get_env


class QuestionAnalysisExecutor(BaseExecutor):
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
        question = row["Question Body"]
        solution = row["Answer HTML"]
        if question == "" or solution == "":
            response = EmptyObject()
            response.content = {}
            return response
        sop_file = SOP_FILE_MAP.get(row["subject"], "SOP-Civil Engg.xlsx")
        df = pd.read_excel(sop_file)
        sop = df.to_string(index=False)
        sop = latex_to_text(sop)
        prompt = self.PROMPT_TEMPLATE.format(
            question=question, solution=solution, sop=sop
        )
        response = await self.analysis_pilot.execute(prompt)
        print(response.content)
        return response

    async def execute(self, **kwargs):
        input_file = kwargs.get("input_file")
        output_file = kwargs.get("output_file")
        df = pd.read_excel(input_file)
        df.fillna("", inplace=True)
        for index, row in df.iterrows():
            response = await self.process_row(row)
            for col_name, col_value in response.content.items():
                df.at[index, col_name] = col_value

        df.to_excel(output_file, index=False)
        return output_file, len(df)

    async def run(self, **kwargs):
        output_file, count = await self.execute(**kwargs)
        return {
            "message": f"file successfully processed",
            "processed_count": count,
        }
