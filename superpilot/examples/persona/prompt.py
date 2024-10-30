
from pydantic import Field
from typing import List, Dict

from superpilot.core.planning import PromptStrategy, LanguageModelClassification, LanguageModelPrompt
from superpilot.core.planning.settings import PromptStrategyConfiguration
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.resource.model_providers import SchemaModel, OpenAIModelName, LanguageModelMessage, MessageRole, \
    LanguageModelFunction


class BaseContent(SchemaModel):
    """
    Class representing a question and its answer as a list of facts each one should have a soruce.
    each sentence contains a body and a list of sources."""

    content: str = Field(
        ..., description="Full body of response content from the llm model"
    )
    highlights: List[str] = Field(
        ...,
        description="Body of the answer, each fact should be its separate object with a body and a list of sources",
    )


class PersonaPrompt(PromptStrategy):
    DEFAULT_SYSTEM_PROMPT = (
        "You should act as a persona given below and respond to the user query from persona's perspective only."
        "You are an expert who can use information effectively. You are chatting with a user who wants to know most important information about the topic. You might have gathered the related information and will now use the information to form a response."
        "Make your response as crisp as possible, ensuring that every sentence is supported by the gathered information. If the [gathered information] is not directly related to the [user query], provide the most relevant response based on the available information."
        "Please don't answer what you have answered before. Your answers should be related to the topic user asked about from your persona's perspective."
        "\n\n"
        "AI Persona:\n"
    )

    DEFAULT_USER_PROMPT_TEMPLATE = (
        # "Context : '{message}'.\n"
        "Context : {context}\n\n"
        "gathered information : '{gathered_information}'.\n\n"
        "user query : '{message}'.\n"
    )

    DEFAULT_PARSER_SCHEMA = BaseContent.function_schema()

    default_configuration = PromptStrategyConfiguration(
        model_classification=LanguageModelClassification.SMART_MODEL,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
        parser_schema=None,
    )

    def __init__(
        self,
        model_classification: LanguageModelClassification = default_configuration.model_classification,
        system_prompt: str = default_configuration.system_prompt,
        user_prompt_template: str = default_configuration.user_prompt_template,
        parser_schema: Dict = None,
    ):
        self._model_classification = model_classification
        self._system_prompt_message = system_prompt
        self._user_prompt_template = user_prompt_template
        self._parser_schema = parser_schema

    @property
    def model_classification(self) -> LanguageModelClassification:
        return self._model_classification

    def build_prompt(self, **kwargs) -> LanguageModelPrompt:
        # print("kwargs",  v)
        model_name = kwargs.pop("model_name", OpenAIModelName.GPT3)
        template_kwargs = self.get_template_kwargs(kwargs)

        system_message = LanguageModelMessage(
            role=MessageRole.SYSTEM,
            content=self._system_prompt_message.format(**template_kwargs),
        )

        if ("images" in template_kwargs
            and template_kwargs.get("images", [])
        ):
            user_message = LanguageModelMessage(
                role=MessageRole.USER,
            )
            # print("VISION prompt", user_message)
            user_message = self._generate_content_list(user_message, template_kwargs)
            print(user_message)
        else:
            user_message = LanguageModelMessage(
                role=MessageRole.USER,
                content=self._user_prompt_template.format(**template_kwargs),
            )

        functions = []
        if self._parser_schema is not None:
            parser_function = LanguageModelFunction(
                json_schema=self._parser_schema,
            )
            functions.append(parser_function)

        # functions.append(
        #     LanguageModelFunction(json_schema=ClarifyingQuestion.function_schema())
        # )

        prompt = LanguageModelPrompt(
            messages=[system_message, user_message],
            functions=functions,
            function_call=None if not functions else functions[0],
            tokens_used=0,
        )
        return prompt

    def get_template_kwargs(self, kwargs):
        template_kwargs = {
            "task_objective": "",
            "cycle_count": 0,
            "action_history": "",
            "additional_info": "",
            "user_input": "",
            "acceptance_criteria": "",
        }
        # Update default kwargs with any provided kwargs
        template_kwargs.update(kwargs)
        return template_kwargs

    def _generate_content_list(self, message: LanguageModelMessage, template_kwargs):
        message.add_text(self._user_prompt_template.format(**template_kwargs))

        image_list = template_kwargs.pop("images", [])
        for image in image_list:
            message.add_image(image, "")
        return message

    def parse_response_content(
        self,
        response_content: dict,
    ) -> dict:
        """Parse the actual text response from the objective model.

        Args:
            response_content: The raw response content from the objective model.

        Returns:
            The parsed response.

        """
        # print("Raw Model Response", response_content)
        if "function_call" in response_content and response_content["function_call"]:
            parsed_response = json_loads(
                response_content.get("function_call", {}).get("arguments", {})
            )
        else:
            parsed_response = response_content

        # print(response_content)
        # parsed_response = json_loads(response_content["content"])
        # parsed_response = self._parser_schema.from_response(response_content)
        return parsed_response

    def get_config(self) -> PromptStrategyConfiguration:
        return PromptStrategyConfiguration(
            model_classification=self._model_classification,
            system_prompt=self._system_prompt_message,
            user_prompt_template=self._user_prompt_template,
            parser_schema=self._parser_schema,
        )

    @classmethod
    def factory(
        cls,
        system_prompt=None,
        user_prompt_template=None,
        parser=None,
        model_classification=None,
    ) -> "PersonaPrompt":
        config = cls.default_configuration.dict()
        if model_classification:
            config["model_classification"] = model_classification
        if system_prompt:
            config["system_prompt"] = system_prompt
        if user_prompt_template:
            config["user_prompt_template"] = user_prompt_template
        if parser:
            config["parser_schema"] = parser
        config.pop("location", None)
        return cls(**config)
