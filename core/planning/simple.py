import logging
import platform
import time
from typing import Dict, List

import distro

from superpilot.core import planning
from superpilot.core.callback.base import BaseCallback
from superpilot.core.callback.manager.base import BaseCallbackManager
from superpilot.core.configuration import Configurable
from superpilot.core.context.schema import Context, Message
from superpilot.core.planning import strategies
from superpilot.core.planning.base import PromptStrategy, Planner
from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelResponse,
    Task, ObjectivePlan,
)
from superpilot.core.planning.settings import (
    PlannerConfigurationLegacy,
    PlannerSettingsLegacy,
    LanguageModelConfiguration,
    PromptStrategiesConfiguration, PlannerSettings, PlannerConfiguration,
)
from superpilot.core.planning.strategies import NextAbility
from superpilot.core.planning.strategies.planning_strategy import PlanningStrategy
from superpilot.core.resource.model_providers import (
    LanguageModelProvider,
    ModelProviderName,
    OpenAIModelName,
)
from superpilot.core.state.base import BaseState
from superpilot.core.workspace import Workspace
from superpilot.core.plugin.utlis import load_class


class SimplePlanner(Configurable, Planner):
    """Manages the pilot's planning and goal-setting by constructing language model prompts."""

    default_settings = PlannerSettings(
        name="planner",
        description="Manages the pilot's planning and goal-setting by constructing language model prompts.",
        configuration=PlannerConfiguration(
            models={
                LanguageModelClassification.FAST_MODEL: LanguageModelConfiguration(
                    model_name=OpenAIModelName.GPT4_O_MINI,
                    provider_name=ModelProviderName.OPENAI,
                    temperature=0.9,
                ),
                LanguageModelClassification.SMART_MODEL: LanguageModelConfiguration(
                    model_name=OpenAIModelName.GPT4_O,
                    provider_name=ModelProviderName.OPENAI,
                    temperature=0.9,
                ),
            },
            planning_strategy=PlanningStrategy.default_configuration,
            execution_strategy=NextAbility.default_configuration,
            reflection_strategy=PlanningStrategy.default_configuration,
        ),
    )

    def __init__(
        self,
        settings: PlannerSettings,
        logger: logging.Logger,
        model_providers: Dict[ModelProviderName, LanguageModelProvider],
        callback: BaseCallbackManager = None,
        workspace: Workspace = None,  # Workspace is not available during bootstrapping.
        context: Context = None,
        state: BaseState = None,
    ) -> None:
        self._configuration = settings.configuration
        self._logger = logger
        self._workspace = workspace
        self._callback = callback
        self._context = context
        self._state = state

        self._providers: Dict[LanguageModelClassification, LanguageModelProvider] = {}
        for model, model_config in self._configuration.models.items():
            self._providers[model] = model_providers[model_config.provider_name]

        self._planning_strategy = self.init_strategy(self._configuration.planning_strategy)
        self._execution_strategy = self.init_strategy(self._configuration.execution_strategy)
        self._reflection_strategy = self.init_strategy(self._configuration.reflection_strategy)

    async def plan(self, user_objective: Task, functions: List[dict], **kwargs) -> ObjectivePlan:
        while True:
            template_kwargs = {"task_objective": user_objective.objective}
            template_kwargs.update(kwargs)
            observation_response = await self.chat_with_model(
                self._planning_strategy,
                functions=functions,
                context=self._context,
                **template_kwargs,
            )
            ability_args = observation_response.content.get("function_arguments", {})
            if ability_args.get("clarifying_question"):
                hold = await self.handle_clarification(observation_response, ability_args, user_objective, **kwargs)
                if hold:
                    self._context.interaction = True
                    await self._state.save(self._context)
                    return None
            else:
                observation = ObjectivePlan(**ability_args)
                break

        return observation

    async def handle_clarification(self, response, ability_args, task, **kwargs) -> bool:
        question_message = Message.add_question_message(
            message=ability_args.get("clarifying_question")
        )
        self._context.add_message(question_message)
        user_input, hold = await self._callback.on_clarifying_question(
            question_message,
            task,
            response,
            self._context,
            **kwargs
        )
        if user_input:
            self._context.add_message(user_input)
        return hold

    async def next(self, task: Task, functions: List[dict], **kwargs) -> LanguageModelResponse:
        return await self.chat_with_model(
            self._execution_strategy,
            task=task,
            ability_schema=functions,
            **kwargs,
        )

    def reflect(self, task: Task, context: Context) -> LanguageModelResponse:
        pass

    async def chat_with_model(
        self,
        prompt_strategy: PromptStrategy,
        **kwargs,
    ) -> LanguageModelResponse:
        model_classification = prompt_strategy.model_classification
        model_configuration = self._configuration.models[model_classification].dict()
        self._logger.debug(f"Using model configuration: {model_configuration}")
        del model_configuration["provider_name"]
        provider = self._providers[model_classification]

        template_kwargs = self._make_template_kwargs_for_strategy(prompt_strategy)
        template_kwargs.update(kwargs)
        prompt = prompt_strategy.build_prompt(**template_kwargs)

        self._logger.debug(f"Using prompt:\n{prompt}\n\n")
        response = await provider.create_language_completion(
            model_prompt=prompt.messages,
            functions=prompt.functions,
            function_call=prompt.get_function_call(),
            req_res_callback=self._callback.model_req_res_callback if self._callback else None,
            **model_configuration,
            completion_parser=prompt_strategy.parse_response_content,
        )
        # return LanguageModelResponse.model_validate(response.model_dump())
        return LanguageModelResponse.parse_obj(response.dict())


    def _make_template_kwargs_for_strategy(self, strategy: PromptStrategy):
        provider = self._providers[strategy.model_classification]
        template_kwargs = {
            "os_info": get_os_info(),
            "api_budget": provider.get_remaining_budget(),
            "current_time": time.strftime("%c"),
        }
        return template_kwargs

    @classmethod
    def init_strategy(cls, prompt_config: PromptStrategiesConfiguration = None):
        prompt_config = prompt_config.dict()
        location = prompt_config.pop("location", None)
        if location is not None:
            return load_class(location, prompt_config)
        else:
            return strategies.NextAbility(**prompt_config)


def get_os_info() -> str:
    os_name = platform.system()
    os_info = (
        platform.platform(terse=True)
        if os_name != "Linux"
        else distro.name(pretty=True)
    )
    return os_info
