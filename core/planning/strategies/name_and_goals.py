import json

from superpilot.core.configuration import SystemConfiguration, UserConfigurable
from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt,
)
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.resource.model_providers import (
    LanguageModelFunction,
    LanguageModelMessage,
    MessageRole,
)


class NameAndGoalsConfiguration(SystemConfiguration):
    model_classification: LanguageModelClassification = UserConfigurable()
    system_prompt: str = UserConfigurable()
    user_prompt_template: str = UserConfigurable()
    create_pilot_function: dict = UserConfigurable()


class NameAndGoals(PromptStrategy):
    DEFAULT_SYSTEM_PROMPT = (
        "Your job is to respond to a user-defined query by invoking the `create_pilot` function "
        "to generate an autonomous pilot info to related to query. \n\n" 
        "The work of this funtion to generate the pilot info and create goals related to query"
        "Response should contain name for the pilot, an informative description for what the pilot does, and 1 to 5 "
        "goals that are optimally aligned with the successful completion of its assigned query.\n\n"
        "Example Input:\n"
        "Help me with marketing my business\n\n"
        "Example Function Call:\n"
        "create_pilot(name='CMOGPT', "
        "description='A professional digital marketer AI that assists Solopreneurs in "
        "growing their businesses by providing world-class expertise in solving "
        "marketing problems for SaaS, content products, agencies, and more.', "
        "goals=['Engage in effective problem-solving, prioritization, planning, and "
        "supporting execution to address your marketing needs as your virtual Chief "
        "Marketing Officer.', 'Provide specific, actionable, and concise advice to "
        "help you make informed decisions without the use of platitudes or overly "
        "wordy explanations.', 'Identify and prioritize quick wins and cost-effective "
        "campaigns that maximize results with minimal time and budget investment.', "
        "'Proactively take the lead in guiding you and offering suggestions when faced "
        "with unclear information or uncertainty to ensure your marketing strategy "
        "remains on track.'])"
    )

    DEFAULT_USER_PROMPT_TEMPLATE = "'{user_objective}'"

    DEFAULT_CREATE_AGENT_FUNCTION = {
        "name": "create_pilot",
        "description": (
            "Create a new autonomous AI pilot to complete a given task."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pilot_name": {
                    "type": "string",
                    "description": "A short role-based name for an autonomous pilot.",
                },
                "pilot_role": {
                    "type": "string",
                    "description": "An informative one sentence description of what the AI pilot does",
                },
                "pilot_goals": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 5,
                    "items": {
                        "type": "string",
                    },
                    "description": (
                        "One to five highly effective goals that are optimally aligned with the completion of a "
                        "specific task. The number and complexity of the goals should correspond to the "
                        "complexity of the pilot's primary objective."
                    ),
                },
            },
            "required": ["pilot_name", "pilot_role", "pilot_goals"],
        },
    }

    default_configuration = NameAndGoalsConfiguration(
        model_classification=LanguageModelClassification.SMART_MODEL,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
        create_pilot_function=DEFAULT_CREATE_AGENT_FUNCTION,
    )

    def __init__(
        self,
        model_classification: LanguageModelClassification,
        system_prompt: str,
        user_prompt_template: str,
        create_pilot_function: str,
    ):
        self._model_classification = model_classification
        self._system_prompt_message = system_prompt
        self._user_prompt_template = user_prompt_template
        self._create_pilot_function = create_pilot_function

    @property
    def model_classification(self) -> LanguageModelClassification:
        return self._model_classification

    def build_prompt(self, user_objective: str = "", **kwargs) -> LanguageModelPrompt:
        system_message = LanguageModelMessage(
            role=MessageRole.SYSTEM,
            content=self._system_prompt_message,
        )
        user_message = LanguageModelMessage(
            role=MessageRole.USER,
            content=self._user_prompt_template.format(
                user_objective=user_objective,
            ),
        )
        create_pilot_function = LanguageModelFunction(
            json_schema=self._create_pilot_function,
        )
        prompt = LanguageModelPrompt(
            messages=[system_message, user_message],
            functions=[create_pilot_function],
            # TODO
            tokens_used=0,
        )
        return prompt

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
        parsed_response = json_loads(response_content["function_call"]["arguments"])
        return parsed_response
