from typing import List

from superpilot.core.configuration import SystemConfiguration, UserConfigurable
from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt,
)
from superpilot.core.planning.strategies.utils import json_loads, to_numbered_list
from superpilot.core.resource.model_providers import (
    LanguageModelFunction,
    LanguageModelMessage,
    MessageRole,
)
from superpilot.core.planning.schema import Task


class StepFlowConfiguration(SystemConfiguration):
    model_classification: LanguageModelClassification = UserConfigurable()
    system_prompt_template: str = UserConfigurable()
    user_prompt_template: str = UserConfigurable()
    system_info: List[str] = UserConfigurable()
    additional_ability_arguments: dict = UserConfigurable()


class StepFlow(PromptStrategy):
    DEFAULT_SYSTEM_PROMPT_TEMPLATE = "System Info:\n{system_info}"

    DEFAULT_SYSTEM_INFO = [
        "The OS you are running on is: {os_info}",
        "The current time and date is {current_time}",
    ]

    DEFAULT_USER_PROMPT_TEMPLATE = """
    Given the query or question: '{query}'\n\n, 
    Generate a series of steps (Min -1 & Max - 3) to process and answer the query comprehensively\n.
    Each Step should be unique and clear and No Two Step can be the same.
    Also Steps should be limited accordingly the scope area of user query.
    Each step should also be associated with an 'ability' that can be executed to fulfill that step. 
    These abilities include actions such as per the below\n\n
    Abilities : \n
    {abilities}\n\n\n
    
    For each step, specify which ability is most appropriate.
    Ensure that the steps are clear, detailed, and well-organized. 
    Ensure that the ability is associated with the correct step.
    Include any necessary context or data that would be required for executing the abilities effectively."
    Your Answer should be in the following format:\n
    {output_schema}\n\n
    Example: \n
    {output_example}\n
    """

    DEFAULT_ADDITIONAL_ABILITY_ARGUMENTS = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The user's query or question"},
            "steps": {
                "type": "array",
                "description": "List of steps according to the flow",
                "items": {
                    "type": "object",
                    "properties": {
                        "step": {
                            "type": "string",
                            "description": "The step that the ability is associated with",
                        },
                        "ability": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the ability",
                                },
                                "arguments": {
                                    "type": "object",
                                    "description": "Arguments for the ability",
                                },
                            },
                            "description": "Details of the ability which needs to be executed for the step",
                        },
                    },
                    "required": ["step", "ability"],
                },
            },
        },
        "required": ["query", "steps"],
    }

    EXAMPLE = {
        "query": "How to file the GSTR1",
        "steps": [
            {
                "step": "Search for information about climate change causes",
                "ability": {
                    "name": "SearchAndSummarize",
                    "arguments": {"query": "Main causes of climate change"},
                },
            },
            {
                "step": "Summarize the findings from the search",
                "ability": {
                    "name": "Summarize",
                    "arguments": {
                        "text": "The main causes of climate change include..."
                    },
                },
            },
            {
                "step": "Compare human activities with natural factors",
                "ability": {
                    "name": "Compare",
                    "arguments": {
                        "items": ["Human activities impact", "Natural factors impact"]
                    },
                },
            },
            {
                "step": "Explain the greenhouse effect",
                "ability": {
                    "name": "Explain",
                    "arguments": {"topic": "Greenhouse effect"},
                },
            },
        ],
    }

    default_configuration = StepFlowConfiguration(
        model_classification=LanguageModelClassification.SMART_MODEL,
        system_prompt_template=DEFAULT_SYSTEM_PROMPT_TEMPLATE,
        system_info=DEFAULT_SYSTEM_INFO,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
        additional_ability_arguments=DEFAULT_ADDITIONAL_ABILITY_ARGUMENTS,
    )

    def __init__(
        self,
        model_classification: LanguageModelClassification,
        system_prompt_template: str,
        system_info: List[str],
        user_prompt_template: str,
        additional_ability_arguments: dict,
    ):
        self._model_classification = model_classification
        self._system_prompt_template = system_prompt_template
        self._system_info = system_info
        self._user_prompt_template = user_prompt_template
        self._additional_ability_arguments = additional_ability_arguments

    @property
    def model_classification(self) -> LanguageModelClassification:
        return self._model_classification

    def build_prompt(
        self,
        query,
        os_info: str,
        **kwargs,
    ) -> LanguageModelPrompt:
        ability_schema = kwargs.get(
            "ability_schema", [{"name": "No ability schema available."}]
        )
        ability_schema = ability_schema[0]
        template_kwargs = {
            "os_info": os_info,
            **kwargs,
        }

        template_kwargs["query"] = query
        template_kwargs["system_info"] = to_numbered_list(
            self._system_info,
            **template_kwargs,
        )
        template_kwargs["abilities"] = ability_schema
        template_kwargs["output_schema"] = self._additional_ability_arguments
        template_kwargs["output_example"] = self.EXAMPLE
        system_prompt = LanguageModelMessage(
            role=MessageRole.SYSTEM,
            content=self._system_prompt_template.format(**template_kwargs),
        )
        user_prompt = LanguageModelMessage(
            role=MessageRole.USER,
            content=self._user_prompt_template.format(**template_kwargs),
        )
        functions = [LanguageModelFunction(json_schema=ability_schema)]

        return LanguageModelPrompt(
            messages=[system_prompt, user_prompt],
            functions=functions,
            # TODO:
            tokens_used=0,
        )

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
        parsed_response = json_loads(response_content["content"])
        return parsed_response
