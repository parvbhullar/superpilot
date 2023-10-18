from typing import Dict, List
from superpilot.core.context.schema import Context
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.examples.executor.base import BaseExecutor
from superpilot.examples.ed_tech.question_solver import (
    QuestionSolverPrompt, Question
)
from superpilot.framework.tools.latex import latex_to_text
from superpilot.framework.helpers.json_utils.utilities import extract_json_from_response
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    AnthropicApiProvider,
    AnthropicModelName
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
                }
        )

    async def run(self, image_path):
        # query = self.image_to_text(image_path)
        query = self.extract_text_from_image(image_path)
        query = query.replace("\\", " ")
        print(query)
        try:
            query = latex_to_text(query)
        except:
            pass
        response = await self.pilot.execute(query)
        # response.content = json_loads(response.content.get("content", "{}"))
        response.content = extract_json_from_response(response.content.get("content", "{}"), Question.function_schema())
        options = self.format_numbered(response.content.get("options", []))
        try:
            response.content["question"] = latex_to_text(response.content.get("question", ""))
        except:
            response.content["question"] = response.content.get("question", "")
        response.content["question"] += f"\n{options}\n"
        response.content["options"] = options
        return response

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
        ACCESS_KEY = 'AKIA5UPPEATFLZART5OB'
        SECRET_KEY = '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'
        import boto3
        client = boto3.client('textract', region_name='ap-south-1', aws_access_key_id=ACCESS_KEY,
                              aws_secret_access_key=SECRET_KEY)

        with open(path, 'rb') as document:
            img_test = document.read()
            image_bytes = bytearray(img_test)
        # response = client.analyze_document(Document={'Bytes': bytes_test}, FeatureTypes=['TABLES'])
        # Call Amazon Textract
        response = client.detect_document_text(Document={'Bytes': image_bytes})

        # Parse the results
        detected_text = []
        for item in response["Blocks"]:
            if item["BlockType"] == "LINE":
                detected_text.append(item["Text"])
        detected_text = "\n".join(detected_text)
        print(detected_text)
        return detected_text

    def format_numbered(self, items) -> str:
        if not items:
            return ""
        return "\n".join([f"{i}) {c}" for i, c in enumerate(items, 1)])

    async def run_list(self, query_list: List[Dict]):
        final_res = []
        try:
            for index, query in enumerate(query_list):
                response = await self.run(query.get("Original Keyword"))
                final_res.append({**query, **response.content})
                print(f"Query {index} finished", "\n\n")
        except Exception as e:
            print(e)
        return final_res
