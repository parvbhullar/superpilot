from typing import List
from superpilot.core.context.schema import Context
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.resource.model_providers.factory import (
    ModelProviderFactory,
)
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

# from superpilot.examples.pilots.tasks.super import SuperTaskPilot
from superpilot.core.resource.model_providers import (
    AnthropicModelName,
    OpenAIModelName,
)
from superpilot.core.resource.model_providers.deepinfra import (
    DeepInfraModelName,
    DeepInfraProvider,
)


class FigureQuestionExecutor(BaseExecutor):
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
        solver_pilot = SimpleTaskPilot.create(
            SolutionValidatorPrompt.default_configuration,
            model_providers=self.model_providers,
            smart_model_name=DeepInfraModelName.WIZARD_LM_8_22B,
            fast_model_name=DeepInfraModelName.WIZARD_LM_8_22B,
        )
        format_pilot = SimpleTaskPilot.create(
            SolutionValidatorPrompt.default_configuration,
            model_providers=self.model_providers,
            smart_model_name=OpenAIModelName.GPT4_TURBO,
            fast_model_name=OpenAIModelName.GPT3,
        )
        # auto_solver_pilot = SuperTaskPilot(super_ability_registry, self.model_providers)
        # print("VISION", vision_pilot)

        # Initialize and add pilots to the chain here, for example:
        self.chain.add_handler(vision_pilot, self.vision_transformer)
        # self.chain.add_handler(auto_solver_pilot, self.auto_solver_transformer)
        self.chain.add_handler(solver_pilot, self.solver_transformer)
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
        response = {
            "question": data,
            "solution": response.get("completion", ""),
        }
        task = self.PROMPT_TEMPLATE.format(**response)
        return task, context

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

    async def execute(self, task: str, **kwargs):
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

        return response

    async def run(self, image_path):
        # query = self.image_to_text(image_path)
        query = self.extract_text_from_image(image_path)
        query = query.replace("\\", " ")
        if not query:
            query = self.image_to_text(image_path)
        if not query:
            return {"solution": "We are unable to process this image"}
        try:
            query = latex_to_text(query)
        except Exception as ex:
            pass
        print(query)
        base64_string = self.image_to_base64(image_path)
        images = [base64_string]
        # print(images)
        response = await self.execute(query, images=images)
        response["solution"] = response.get("solution", "").replace("&", " ")
        # print(response)
        return response

    # Function to get base64 string from image file
    def image_to_base64(self, image_path):
        import base64

        # Infer the image type from the file extension
        image_type = image_path.split(".")[-1].lower()
        # Determine the correct MIME type
        if image_type == "png":
            mime_type = "image/png"
        elif image_type in ["jpg", "jpeg"]:
            mime_type = "image/jpeg"
        elif image_type == "gif":
            mime_type = "image/gif"
        else:
            raise ValueError("Unsupported image type")

        # Open the image file in binary read mode
        with open(image_path, "rb") as image_file:
            # Read the image file
            image_data = image_file.read()
            # Encode the image data using base64
            base64_encoded_data = base64.b64encode(image_data)
            # Format with the prefix for data URI scheme
            base64_image = (
                f"data:{mime_type};base64,{base64_encoded_data.decode('utf-8')}"
            )
            return base64_image

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
        # print(r.text, "Mathpix response")
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
