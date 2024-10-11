import os
from typing import Dict, List
from superpilot.core.context.schema import Context
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.resource.model_providers.factory import (
    ModelProviderFactory,
)
from superpilot.examples.ed_tech.answer_categorizer import AnswerCategorizerPrompt
from superpilot.examples.executor.base import BaseExecutor
from superpilot.examples.ed_tech.solution_validator import SolutionValidatorPrompt
from superpilot.examples.ed_tech.describe_image_question import DescribeQFigurePrompt
from superpilot.framework.tools.latex import latex_to_text
from superpilot.tests.test_env_simple import get_env
from superpilot.core.configuration.config import get_config
from superpilot.core.pilot.chain.simple import SimpleChain

# from superpilot.examples.pilots.tasks.super import SuperTaskPilot
from superpilot.core.resource.model_providers import OpenAIModelName
from superpilot.core.resource.model_providers.deepinfra import DeepInfraModelName


class FigureQuestionExecutor(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()
    context = Context()
    config = get_config()
    env = get_env({})

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.chain = SimpleChain()

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
        # solver_pilot = SimpleTaskPilot.create(
        #     SolutionValidatorPrompt.default_configuration,
        #     model_providers=self.model_providers,
        #     smart_model_name=OpenAIModelName.GPT4_O,
        #     fast_model_name=OpenAIModelName.GPT4_O,
        # )
        # format_pilot = SimpleTaskPilot.create(
        #     SolutionValidatorPrompt.default_configuration,
        #     model_providers=self.model_providers,
        #     smart_model_name=OpenAIModelName.GPT4_O,
        #     fast_model_name=OpenAIModelName.GPT4_O,
        # )
        # auto_solver_pilot = SuperTaskPilot(super_ability_registry, self.model_providers)
        # print("VISION", vision_pilot)

        # Initialize and add pilots to the chain here, for example:
        self.chain.add_handler(vision_pilot, self.vision_transformer)
        self.chain.add_handler(solver_pilot, self.solver_transformer)

        self.answer_pilot = SimpleTaskPilot.create(
            AnswerCategorizerPrompt().get_config(),
            model_providers=self.model_providers,
            smart_model_name=OpenAIModelName.GPT4_O,
            fast_model_name=OpenAIModelName.GPT4_O,
        )
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
            "solution": response.get("content", ""),
        }
        # task = self.PROMPT_TEMPLATE.format(**response)
        # return task, context
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

    async def execute(self, task: str, **kwargs):
        response, context = await self.chain.execute(task, self.context, **kwargs)
        response["total_cost"] = self.chain.total_cost

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
        if os.path.exists(image_path) and os.path.isfile(image_path):
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
            base64_string = self.image_to_base64(image_path)
            images = [base64_string]
        else:
            query = image_path
            images = []
            from superpilot.core.pilot.chain.base import HandlerType

            if "vision" in str(self.chain.pilots[HandlerType.HANDLER][0]):
                self.chain.remove_handler(0)

        print("FigureQuestionExecutor  Query --> ", query)
        # print(images)
        response = await self.execute(query, images=images)
        if isinstance(response, str):
            response = {"solution": response}
        response["solution"] = response.get("solution", "").replace("&", " ")
        # solution = response.get("solution", "")
        # sol_res = await self.answer_pilot.execute(
        #     solution, response_format={"type": "json_object"}
        # )
        # response["solution_categorized"] = sol_res.content
        # self.chain.update_cost(sol_res)
        # response["total_cost"] = self.chain.total_cost
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

    async def run_list(self, query_list: List[Dict]):
        final_res = []
        error_res = []
        for index, query in enumerate(query_list):
            try:
                response = await self.run(query.get("Question Content"))
                print(response.get("total_cost"))
                final_res.append(
                    {
                        **query,
                        **response.copy(),
                        "total_cost$": response.get("total_cost", {}).get(
                            "total_cost", 0
                        ),
                    }
                )
                print(f"Query {index} finished", "\n\n")
            except Exception as e:
                try:
                    print("Trying to run again")
                    response = await self.run(query.get("Question Content"))
                    final_res.append(
                        {
                            **query,
                            **response.copy(),
                            "total_cost$": response.get("total_cost", {}).get(
                                "total_cost", 0
                            ),
                        }
                    )
                    print(f"Query {index} finished", "\n\n")
                except Exception as e:
                    print(e, "Query Failed")
                    error_res.append(query)
        return final_res, error_res
