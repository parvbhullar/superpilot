from typing import List
from superpilot.core.context.schema import Context
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.examples.executor.base import BaseExecutor
from superpilot.examples.ed_tech.question_solver import QuestionSolverPrompt
from superpilot.framework.tools.latex import latex_to_text
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    AnthropicModelName,
)
from superpilot.core.planning.settings import (
    LanguageModelConfiguration,
    LanguageModelClassification,
)


class QuestionExecutor(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()
    context = Context()

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.super_prompt = QuestionSolverPrompt.factory()
        self.pilot = SimpleTaskPilot.factory(
            prompt_strategy=self.super_prompt.get_config(),
            model_providers=self.model_providers,
            models={
                LanguageModelClassification.FAST_MODEL: LanguageModelConfiguration(
                    model_name=AnthropicModelName.CLAUD_2_INSTANT,
                    provider_name=ModelProviderName.ANTHROPIC,
                    temperature=1,
                ),
                LanguageModelClassification.SMART_MODEL: LanguageModelConfiguration(
                    model_name=AnthropicModelName.CLAUD_2,
                    provider_name=ModelProviderName.ANTHROPIC,
                    temperature=0.9,
                ),
            },
        )

    async def run(self, image_path):
        # query = self.image_to_text(image_path)
        query = self.extract_text_from_image(image_path)
        query = query.replace("\\", " ")
        print(query)
        try:
            query = latex_to_text(query)
        except Exception as ex:
            pass
        response = await self.pilot.execute(query)
        result = {"question": query, "solution": response.content.get("completion", "")}
        return result

    def image_to_text(self, image_path):
        from PIL import Image
        import pytesseract

        # Load the image from file
        img_path = image_path
        img = Image.open(img_path)
        # Use Tesseract to do OCR on the image
        text = pytesseract.image_to_string(img)
        return text

    def extract_text_from_image(self, path):
        # !/usr/bin/env python
        import requests
        import json
        import os

        r = requests.post(
            "https://api.mathpix.com/v3/text",
            files={"file": open(path, "rb")},
            data={
                "options_json": json.dumps(
                    {"math_inline_delimiters": ["$", "$"], "rm_spaces": True}
                )
            },
            headers={
                "app_id": os.environ.get("MATHPIX_APP_ID"),
                "app_key": os.environ.get("MATHPIX_APP_KEY"),
            },
        )
        return r.json().get("text", "")

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
