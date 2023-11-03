import logging
import time
from typing import List, Dict

from superpilot.core.pilot.task.base import TaskPilot, TaskPilotConfiguration
from superpilot.core.context.schema import Context
from superpilot.core.ability.base import AbilityRegistry
from superpilot.core.plugin.simple import (
    PluginLocation,
    PluginStorageFormat,
)
from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning import strategies
from superpilot.core.planning.schema import (
    LanguageModelResponse,
    ExecutionNature,
    Task,
)
from superpilot.core.planning.settings import (
    LanguageModelConfiguration,
    LanguageModelClassification,
)
from superpilot.core.resource.model_providers import (
    LanguageModelProvider,
    ModelProviderName,
    OpenAIModelName,
)
from superpilot.framework.helpers.system import get_os_info


class BaseTaskPilot(TaskPilot):
    default_configuration = TaskPilotConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.BaseTaskPilot",
        ),
        execution_nature=ExecutionNature.SEQUENTIAL,
        prompt_strategy=strategies.NextAbility.default_configuration,
        models={
            LanguageModelClassification.FAST_MODEL: LanguageModelConfiguration(
                model_name=OpenAIModelName.GPT3,
                provider_name=ModelProviderName.OPENAI,
                temperature=0.9,
            ),
            LanguageModelClassification.SMART_MODEL: LanguageModelConfiguration(
                model_name=OpenAIModelName.GPT4,
                provider_name=ModelProviderName.OPENAI,
                temperature=0.9,
            ),
        },
    )

    def __init__(
        self,
        ability_registry: AbilityRegistry,
        model_providers: Dict[ModelProviderName, LanguageModelProvider],
        configuration: TaskPilotConfiguration = default_configuration,
        logger: logging.Logger = logging.getLogger(__name__),
    ) -> None:
        self._logger = logger
        self._configuration = configuration
        self._execution_nature = configuration.execution_nature
        self._ability_registry = ability_registry

        self._providers: Dict[LanguageModelClassification, LanguageModelProvider] = {}
        for model, model_config in self._configuration.models.items():
            self._providers[model] = model_providers[model_config.provider_name]

        self._prompt_strategy = strategies.NextAbility(
            **self._configuration.prompt_strategy.dict()
        )

    async def execute(
        self, task: Task | str, context_res: Context, *args, **kwargs
    ) -> Context:
        if isinstance(task, str):
            task = Task.factory(task, **kwargs)
        for ability in self._ability_registry.abilities():
            context_res = await self.perform_ability(
                task, [ability.dump()], context_res, **kwargs
            )
        return context_res

    async def perform_ability(
        self, task: Task, ability_schema: List[dict], context, **kwargs
    ) -> Context:
        if self._execution_nature == ExecutionNature.AUTO:
            response = await self.determine_next_ability(
                task, ability_schema, context=context.format_numbered(), **kwargs
            )
        else:
            response = await self.determine_exec_ability(
                task, ability_schema, context=context.format_numbered(), **kwargs
            )
        ability_args = response.content.get("ability_arguments", {})
        ability_action = await self._ability_registry.perform(
            response.content["next_ability"],
            **ability_args,
            context=context.format_numbered(),
            task=task,
        )
        if ability_action:
            context.extend(ability_action.knowledge)
        return context

    async def determine_exec_ability(
        self, task: Task, ability_schema: List[dict], **kwargs
    ) -> LanguageModelResponse:
        return await self.chat_with_model(
            self._prompt_strategy,
            task=task,
            ability_schema=ability_schema,
            **kwargs,
        )

    async def determine_next_ability(
        self, task: Task, ability_schema: List[dict], **kwargs
    ) -> LanguageModelResponse:
        return await self.chat_with_model(
            self._prompt_strategy,
            task=task,
            ability_schema=ability_schema,
            **kwargs,
        )

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
            **model_configuration,
            completion_parser=prompt_strategy.parse_response_content,
        )
        return LanguageModelResponse.parse_obj(response.dict())

    def _make_template_kwargs_for_strategy(self, strategy: PromptStrategy):
        provider = self._providers[strategy.model_classification]
        template_kwargs = {
            "os_info": get_os_info(),
            "api_budget": provider.get_remaining_budget(),
            "current_time": time.strftime("%c"),
        }
        return template_kwargs

    def __repr__(self):
        return f"{self.__class__.__name__}()"
