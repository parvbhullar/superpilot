from typing import List
from superpilot.core.configuration import SystemConfiguration, UserConfigurable
from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt,
    Task, TaskStatus, ClarifyingQuestion, Reflection,
)
from superpilot.core.planning.strategies.utils import json_loads, to_numbered_list
from superpilot.core.resource.model_providers import (
    LanguageModelFunction,
    LanguageModelMessage,
    MessageRole,
)
from superpilot.core.context.schema import Context


class NextAbilityConfiguration(SystemConfiguration):
    model_classification: LanguageModelClassification = UserConfigurable()
    system_prompt_template: str = UserConfigurable()
    system_info: List[str] = UserConfigurable()
    user_prompt_template: str = UserConfigurable()
    additional_ability_arguments: dict = UserConfigurable()


class NextAbility(PromptStrategy):
    DEFAULT_SYSTEM_PROMPT_TEMPLATE = "System Info:\n{system_info}"

    DEFAULT_SYSTEM_INFO = [
        "The OS you are running on is: {os_info}",
        "It takes money to let you run. Your API budget is ${api_budget:.3f}",
        "The current time and date is {current_time}",
    ]

    # TODO: add he prompt template system message to make assistant understand the structure of conversation
    DEFAULT_USER_PROMPT_TEMPLATE = """
    *Context*: {context}

    Make function arguments for the function *'{function_name}'* according to the context provided.
    """

    DEFAULT_ADDITIONAL_ABILITY_ARGUMENTS = {
        "motivation": {
            "type": "string",
            "description": "Your justification for choosing choosing this function parameters instead of a different one.",
        },
        "self_criticism": {
            "type": "string",
            "description": "Thoughtful self-criticism that explains why this function parameters may not be the best "
                           "choice.",
        },
        "reasoning": {
            "type": "string",
            "description": "Your reasoning for choosing this function parameters into account the `motivation` "
                           "and weighing the `self_criticism`.",
        },
        # "task_status": {
        #     "type": "string",
        #     "description": "overall status of the task, on hold if ambiguous, "
        #                    "ready if all the acceptance criteria are met",
        #     "enum": [t for t in TaskStatus],
        # },
        # 'task_objective': {
        #     "type": "string",
        #     "description": "verbose description of the current sub task you will be performing. this should be "
        #                    "current task not the whole objective",
        # },
        "ambiguity": {
            "type": "array",
            "description": "your thoughtful reflection on the ambiguity of the task",
            "items": {
                "type": "string",
                "description": "your thoughtful reflection on the ambiguity of the task"
            }
        }
    }

    default_configuration = NextAbilityConfiguration(
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

        # TODO add logger here

    @property
    def model_classification(self) -> LanguageModelClassification:
        return self._model_classification

    def build_prompt(
            self,
            task: Task,
            ability_schema: List[dict],
            os_info: str,
            api_budget: float,
            current_time: str,
            context: Context,
            **kwargs,
    ) -> LanguageModelPrompt:
        template_kwargs = {
            "os_info": os_info,
            "api_budget": api_budget,
            "current_time": current_time,
            **kwargs,
        }

        # context = kwargs.get("context", Context())
        # print("Context: ", type(context))

        for ability in ability_schema:
            ability["parameters"]["properties"].update(
                self._additional_ability_arguments
            )
            ability["parameters"]["required"] += list(
                self._additional_ability_arguments.keys()
            )

        template_kwargs["system_info"] = to_numbered_list(
            self._system_info,
            **template_kwargs,
        )

        # template_kwargs['task_objective'] = task.objective
        template_kwargs["context"] = context

        system_prompt = LanguageModelMessage(
            role=MessageRole.SYSTEM,
            content=self._system_prompt_template.format(**template_kwargs),
        )
        user_prompt = LanguageModelMessage(
            role=MessageRole.USER,
            content=self._user_prompt_template.format(**template_kwargs),
        )
        # functions = [
        #     LanguageModelFunction(json_schema=ability) for ability in ability_schema
        # ]
        # 
        # functions.append(LanguageModelFunction(json_schema=ClarifyingQuestion.function_schema()))
        # functions.append(LanguageModelFunction(json_schema=Reflection.function_schema()))

        function = {
            "name": "execute_functions",
            "description": "versatile function wrapper designed to execute multiple functions based on a structured "
                           "object passed as its argument. This function simplifies the process of calling multiple "
                           "functions with varying parameters by organizing the function calls and their respective "
                           "parameters in a single, unified structure.",
            "parameters": {
                "type": "object",
                "properties": {},
                # "required": ["ClarifyingQuestion", "PilotObservation"]
            }
        }

        # for schema in [
        #     ClarifyingQuestion.function_schema(arguments_format=True),
        # ]:
        #     function["parameters"]["properties"].update(
        #         schema
        #     )

        for ability in ability_schema:
            function["parameters"]["properties"].update({
                ability.get("name"): {
                    "description": ability.get("description"),
                    **ability.get("parameters", {})
                }
            })

        function = LanguageModelFunction(json_schema=function)
        functions = [function]

        return LanguageModelPrompt(
            messages=[system_prompt, user_prompt],
            functions=functions,
            function_call=function,
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
        # function_name = response_content.get("function_call", {}).get("name")
        # function_arguments = json_loads(response_content.get("function_call", {}).get("arguments", "{}"))
        # parsed_response = {
        #     "motivation": function_arguments.pop("motivation", None),
        #     "self_criticism": function_arguments.pop("self_criticism", None),
        #     "reasoning": function_arguments.pop("reasoning", None),
        #     "task_status": function_arguments.pop("task_status", None),
        #     "task_objective": function_arguments.pop("task_objective", None),
        #     "ambiguity": function_arguments.pop("ambiguity", None),
        #     "next_ability": function_name,
        #     "ability_arguments": function_arguments,
        # }
        # # self._logger.debug(f"Next ability parsed response: {parsed_response}")
        # print(f"Next ability response: {parsed_response}")
        # return parsed_response

        args = json_loads(response_content["function_call"]["arguments"])
        if args.get("ClarifyingQuestion"):
            function_name = "ClarifyingQuestion"
            function_arguments = args["ClarifyingQuestion"]
        else:
            function_name = list(args.keys())[0]
            function_arguments = args[list(args.keys())[0]] if args else {}
        parsed_response = {
            "motivation": function_arguments.pop("motivation", None),
            "self_criticism": function_arguments.pop("self_criticism", None),
            "reasoning": function_arguments.pop("reasoning", None),
            # "task_status": function_arguments.pop("task_status", None),
            # "task_objective": function_arguments.pop("task_objective", None),
            "ambiguity": function_arguments.pop("ambiguity", None),
            "function_name": function_name,
            "function_arguments": function_arguments,
        }

        # print(response_content)
        # parsed_response = json_loads(response_content["content"])
        # parsed_response = self._parser_schema.from_response(response_content)
        return parsed_response
