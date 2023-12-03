import asyncio
import json
import logging
import platform
import time
from typing import List, Dict

from services.gstgptservice.agents.gstr1_filing.abilities.observer_ability import ObserverAbility
from services.gstgptservice.agents.gstr1_filing.pilots.observer import observer
from superpilot.core.pilot.task.base import TaskPilot, TaskPilotConfiguration
from superpilot.core.context.schema import Context, Content, ContentType
from superpilot.core.ability.base import AbilityRegistry
from superpilot.core.plugin.simple import (
    PluginLocation,
    PluginStorageFormat,
    SimplePluginService,
)
import distro
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
    PromptStrategiesConfiguration,
)
from superpilot.core.resource.model_providers import (
    LanguageModelProvider,
    ModelProviderName,
    OpenAIModelName,
)
from superpilot.core.pilot.settings import (
    PilotConfiguration,
    ExecutionAlgo
)
from superpilot.core.resource.model_providers.factory import ModelProviderFactory, ModelConfigFactory


class SuperPilot(TaskPilot):

    default_configuration = TaskPilotConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="services.gstgptservice.agents.gstr1_filing.pilots.super_pilot.SuperPilot",
        ),
        pilot=PilotConfiguration(
            name="super_task_pilot",
            role=(
                "An AI Pilot designed to complete gstr1 filing with masters India"
            ),
            goals=[
                "Transform any json data to gstr 1 filing data",
                "Call an api to push the filing data",
                "Get the response from api and confirm with user",
                "If user confirms, then file the gstr 1",
            ],
            cycle_count=0,
            max_task_cycle_count=3,
            creation_time="",
            execution_algo=ExecutionAlgo.PLAN_AND_EXECUTE,
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
                model_name=OpenAIModelName.GPT4_TURBO,
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

    async def execute(self, objective: str, *args, **kwargs) -> Context:
        """Execute the task."""
        self._logger.debug(f"Executing task: {objective}")
        task = Task.factory(objective, **kwargs)
        if len(args) > 0:
            kwargs["context"] = args[0]
        context_res = await self.exec_task(task, **kwargs)

        return context_res

    async def exec_task(self, task: Task, **kwargs) -> Context:
        context_res = kwargs.pop("context", Context())
        if self._execution_nature == ExecutionNature.PARALLEL:
            tasks = [
                self.perform_ability(task, [ability.dump()], context_res, **kwargs)
                for ability in self._ability_registry.abilities()
            ]
            res_list = await asyncio.gather(*tasks)
            for response in res_list:
                context_res.extend(response)
        elif self._execution_nature == ExecutionNature.AUTO:
            user_input = f"Latest User input {task.objective}"
            context = Context([Content.add_content_item(user_input, ContentType.TEXT, )])
            context_res.extend(context)
            # user_input = f"You have following functions provided \n {self._ability_registry.dump_abilities()}"
            # context = Context([Content.add_content_item(user_input, ContentType.TEXT, )])
            # context_res.extend(context)
            errors_count = 0
            while True:
                # output will be in form of terminal(print)
                # try yo convet observer to ability -> wil be called mannualy onky...not passed to context
                # Observer Ability is asistent ability
                observer_ability = ObserverAbility(environment=self._ability_registry._environment)
                observer_task = Task.factory(
                    """
                        Based on the given context:
                        1. identify if any user input/question is required if yes then ask for the same from user
                        2. return if there is any relevant response that can be given to user
                        3. please set call_function true if you think based on current context we can call function
                        4. set is_exit true if you think user wants to exit
                    """
                )
                # observer_response = await observer(context_res)
                next_ability, ability_args = await self.perform_ability(
                    observer_task, [observer_ability.dump()], context_res, **kwargs
                )

                # if ability_args.get('observer_response', {}).get('is_error'):
                #     errors_count += 1
                #     if errors_count > 3:
                #         return context_res
                # else:
                #     errors_count = 0

                
                if ability_args.get('observer_response', {}).get('is_exit'):
                    return context_res

                if ability_args.get('observer_response', {}).get('info'):
                    info_to_user = f"Response to user: {ability_args.get('observer_response', {}).get('info')}"
                    context = Context([Content.add_content_item(info_to_user, ContentType.TEXT, )])
                    context_res.extend(context)
                    print(info_to_user)
                
                if ability_args.get('observer_response', {}).get('question'):
                    print(ability_args.get('observer_response', {}).get('question'))
                    user_input = input() # add proxy agent here (TAxFilingAgent)
                    question = f"Question: {ability_args.get('observer_response', {}).get('question')}"
                    context = Context([Content.add_content_item(question, ContentType.TEXT, )])
                    context_res.extend(context)
                    user_input = f"Latest User Input: {user_input}"
                    context = Context([Content.add_content_item(user_input, ContentType.TEXT, )])
                    context_res.extend(context)
                    continue
                
                if ability_args.get('observer_response', {}).get('call_function'):
                    next_ability, ability_args = await self.perform_ability(
                        task, self._ability_registry.dump_abilities(), context_res, **kwargs
                    )
                    ability_action = await self._ability_registry.perform(
                        next_ability, **ability_args
                    )
                    context = ability_action.knowledge
                    context_res.extend(context)
                    continue


                question = "Do you need more assistant?"
                context = Context([Content.add_content_item(question, ContentType.TEXT, )])
                context_res.extend(context)
                print(question)
                user_input = input()
                user_input = f"Latest User Input: {user_input}"
                context = Context([Content.add_content_item(user_input, ContentType.TEXT, )])
                context_res.extend(context)
                #     Find ability anyway and of anulity bkt found, ask the questuon again
                
                
                # TODO: exist based upon is_exit
                # if not context.items:
                #     break
                # else:
                #     context_res.extend(context)
                #   add observer
        else:
            # Execute for Sequential nature
            for ability in self._ability_registry.abilities():
                # print(res.content)
                context_res = await self.perform_ability(
                    task, [ability.dump()], context_res, **kwargs
                )
                # TODO add context to task prior actions as ability action.
                # task.
        return context_res

    async def perform_ability(
        self, task: Task, ability_schema: List[dict], context, **kwargs
    ) -> tuple:
        print('Hello')
        if self._execution_nature == ExecutionNature.AUTO:
            response = await self.determine_next_ability(
                task, ability_schema, context=context, **kwargs
            )
        else:
            response = await self.determine_exec_ability(
                task, ability_schema, context=context, **kwargs
            )
        if not response.content.get("next_ability"):
            return Context()
        ability_args = response.content.get("ability_arguments", {})
        next_ability = response.content.get("next_ability")
        return next_ability, ability_args

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
        print(f"Using model configuration: {model_configuration}")
        del model_configuration["provider_name"]
        provider = self._providers[model_classification]

        template_kwargs = self._make_template_kwargs_for_strategy(prompt_strategy)
        template_kwargs.update(kwargs)
        prompt = prompt_strategy.build_prompt(**template_kwargs)

        self._logger.debug(f"Using prompt:\n{prompt}\n\n")
        print(f"Using prompt:\n{prompt}\n\n")
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
        return f"SuperTaskPilot({self._configuration})"

    @classmethod
    def create(cls,
               prompt_config,
               smart_model_name=OpenAIModelName.GPT4,
               fast_model_name=OpenAIModelName.GPT3,
               smart_model_temp=0.9,
               fast_model_temp=0.9,
               model_providers=None):

        models_config = ModelConfigFactory.get_models_config(
            smart_model_name=smart_model_name,
            fast_model_name=fast_model_name,
            smart_model_temp=smart_model_temp,
            fast_model_temp=fast_model_temp,
        )
        if model_providers is None:
            model_providers = ModelProviderFactory.load_providers()

        pilot = cls.factory(
            prompt_strategy=prompt_config,
            model_providers=model_providers,
            models=models_config,
        )
        return pilot


def get_os_info() -> str:
    os_name = platform.system()
    os_info = (
        platform.platform(terse=True)
        if os_name != "Linux"
        else distro.name(pretty=True)
    )
    return os_info
