import abc
import enum
import json
import os
from datetime import datetime, time
from typing import List, Any, Dict
import logging
import platform
from abc import ABC

import distro

from superpilot.core.configuration import SystemConfiguration
from superpilot.core.pilot.base import BasePilot
from superpilot.core.pilot.settings import PilotConfiguration, ExecutionNature
from superpilot.core.planning import LanguageModelClassification, LanguageModelResponse, PromptStrategy
from superpilot.core.planning.settings import LanguageModelConfiguration
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.plugin.utlis import load_class
from superpilot.core.resource.model_providers import LanguageModelProvider, OpenAIModelName, OPEN_AI_MODELS
from superpilot.core.resource.model_providers.factory import ModelProviderFactory, ModelConfigFactory
from superpilot.examples.persona.prompt import PersonaPrompt
from superpilot.examples.persona.schema import Message, Context
from superpilot.examples.persona.vector_service import Retriever, ServiceRM
from superpilot.framework.llm import count_string_tokens
import inflection

SEARCH_SERVICE_URL = os.getenv("SEARCH_SERVICE_URL")

class RoleConfiguration(SystemConfiguration):
    name: str
    role: str
    creation_time: str
    cycle_count: int
    max_task_cycle_count: int

class HandlerConfiguration(SystemConfiguration):
    """Struct for model configuration."""
    location: PluginLocation
    role: RoleConfiguration = None
    execution_nature: ExecutionNature = ExecutionNature.AUTO
    models: Dict[LanguageModelClassification, LanguageModelConfiguration] = None
    callbacks: List[PluginLocation] = None
    prompt_strategy: SystemConfiguration = None
    memory_provider_required: bool = False
    workspace_required: bool = False


class BaseHandler(abc.ABC):
    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    async def execute(self, *args, **kwargs):
        ...

    # @abc.abstractmethod
    # async def observe(self, *args, **kwargs):
    #     ...

    @abc.abstractmethod
    def __repr__(self):
        ...

    @classmethod
    def name(cls) -> str:
        """The name of the ability."""
        return inflection.underscore(cls.__name__)

    @abc.abstractmethod
    def dump(self):
        ...
class PersonaHandler(BaseHandler, ABC):
    """A class representing a handler step."""

    default_configuration = HandlerConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="super.apps.ais_app.agents.base.PersonaHandler",
        ),
        role=RoleConfiguration(
            name="persona_handler",
            role="A handler to handle user queries based on given persona.",
            cycle_count=0,
            max_task_cycle_count=3,
            creation_time=datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
        ),
        execution_nature=ExecutionNature.AUTO,
    )

    def __init__(
            self,
            configuration: HandlerConfiguration = default_configuration,
            logger: logging.Logger = logging.getLogger(__name__),
            model_providers: Dict[str, LanguageModelProvider] = None,
            session_id: str = None,
    ) -> None:
        self._session_id = session_id
        self._logger = logger
        self._configuration = configuration
        self._execution_nature = configuration.execution_nature
        self._agent_data = {}

        self._providers: Dict[LanguageModelClassification, LanguageModelProvider] = {}
        if model_providers is None:
            model_providers = ModelProviderFactory.load_providers()
        for model, model_config in self._configuration.models.items():
            self._providers[model] = model_providers[model_config.provider_name]

        prompt_config = self._configuration.prompt_strategy.dict()
        location = prompt_config.pop("location", None)
        if location is not None:
            self._prompt_strategy = load_class(location, prompt_config)
        else:
            self._prompt_strategy = PersonaPrompt(**prompt_config)

        self.retriever = Retriever(rm=ServiceRM(SEARCH_SERVICE_URL))


    async def execute(
        self, objective: str | Message, *args, **kwargs
    ) -> LanguageModelResponse:
        """Execute the task."""
        self._logger.debug(f"Executing task: {objective}")
        if not isinstance(objective, Message):
            # if task is not passed, one is created with default settings
            task = Message.create(objective)
        else:
            task = objective
        context = kwargs.get('context', None)
        if len(args) > 0:
            context = args[0]
        if context is None:
            context = Context(task.session_id, [task])

        context_res = await self.exec_task(task, context, **kwargs)
        return context_res


    async def exec_task(self, message: Message, context:Context, **kwargs) -> LanguageModelResponse:
        ## TODO fetch data from store service from those knowledge bases and update the template_kwargs
        # Call the retriever on a particular query.
        kn_bases = self._agent_data.get('knowledge_bases',
                                        ['U83Y7PIIL1CICBT6LTVKNXRA'])  # TODO remove hardcoded knowledge base
        info = self.retriever.search(message.message, kn_bases=[])

        template_kwargs = message.generate_kwargs()
        template_kwargs.update(kwargs)
        template_kwargs['gathered_information'] = info
        template_kwargs['context'] = context.summary()

        return await self.chat_with_model(
            self._prompt_strategy,
            **template_kwargs,
        )

    async def chat_with_model(
        self,
        prompt_strategy: PromptStrategy,
        **kwargs,
    ) -> LanguageModelResponse:
        model_classification = prompt_strategy.model_classification
        model_configuration = self._configuration.models[model_classification]

        template_kwargs = self._make_template_kwargs_for_strategy(prompt_strategy)
        kwargs.update(template_kwargs)
        prompt = prompt_strategy.build_prompt(
            model_name=model_configuration.model_name, **kwargs
        )
        # print("Prompt", prompt)
        model_configuration = self.choose_model(
            model_classification, model_configuration, prompt
        )

        model_configuration = model_configuration.dict()
        self._logger.debug(f"Using model configuration: {model_configuration}")
        del model_configuration["provider_name"]
        provider = self._providers[model_classification]
        if "response_format" in kwargs:
            model_configuration["response_format"] = kwargs["response_format"]

        self._logger.debug(f"Using prompt:\n{prompt}\n\n")
        response = await provider.create_language_completion(
            model_prompt=prompt.messages,
            functions=prompt.functions,
            function_call=prompt.get_function_call(),
            # req_res_callback=(
            #     self._callback.model_req_res_callback if self._callback else None
            # ),
            **model_configuration,
            completion_parser=prompt_strategy.parse_response_content,
        )

        return LanguageModelResponse.parse_obj(response.dict())

    def choose_model(self, model_classification, model_configuration, prompt):
        if model_configuration.model_name not in [
            OpenAIModelName.GPT3,
            OpenAIModelName.GPT4,
        ]:
            return model_configuration
        current_tokens = count_string_tokens(
            str(prompt), model_configuration.model_name
        )
        print("Tokens", current_tokens)
        token_limit = OPEN_AI_MODELS[model_configuration.model_name].max_tokens
        completion_token_min_length = 1000
        send_token_limit = token_limit - completion_token_min_length
        if current_tokens > send_token_limit:
            if model_classification == LanguageModelClassification.FAST_MODEL:
                model_configuration.model_name = OpenAIModelName.GPT4_O_MINI
            elif model_classification == LanguageModelClassification.SMART_MODEL:
                print("Using GPT4_TURBO")
                model_configuration.model_name = OpenAIModelName
        return model_configuration

    def _make_template_kwargs_for_strategy(self, strategy: PromptStrategy):
        provider = self._providers[strategy.model_classification]
        template_kwargs = {
            "os_info": get_os_info(),
            "api_budget": provider.get_remaining_budget(),
            "current_time": datetime.strftime(datetime.now(), "%c"),
        }
        return template_kwargs

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __str__(self):
        return self._configuration.__str__()

    def name(self) -> str:
        """The name of the ability."""
        return self._configuration.role.name

    def dump(self) -> dict:
        role_config = self._configuration.role
        dump = {
            "name": role_config.name,
            "role": role_config.role,
            "agent_data": self._agent_data,
            # "prompt_strategy": self._prompt_strategy.get_config().__dict__
        }
        return dump

    @classmethod
    def from_json(cls, json_data: str|dict) -> "PersonaHandler":
        if isinstance(json_data, dict):
            data = json_data
        else:
            data = json.loads(json_data)
        fields = data.get('fields', data)

        models_config = ModelConfigFactory.get_models_config(
            smart_model_name=fields.get('smart_model_name', OpenAIModelName.GPT4_O_MINI),
            fast_model_name=fields.get('fast_model_name', OpenAIModelName.GPT4),
            smart_model_temp=fields.get('smart_model_temp', 0.2),
            fast_model_temp=fields.get('fast_model_temp', 0.2),
        )

        system_prompt = (PersonaPrompt.DEFAULT_SYSTEM_PROMPT + "\\n"
                         + fields.get('about', '')
                         + "\\n" + fields.get('persona', ''))
        prompt_strategy = PersonaPrompt.factory(
            system_prompt=system_prompt,
            user_prompt_template=PersonaPrompt.DEFAULT_USER_PROMPT_TEMPLATE,
        )

        configuration = HandlerConfiguration(
            location=PluginLocation(
                storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                storage_route="super.apps.ais_app.pilot.base.PersonaHandler",
            ),
            role=RoleConfiguration(
                name=fields.get('persona_name', ''),
                role=fields.get('about', ''),
                cycle_count=0,
                max_task_cycle_count=3,
                creation_time=datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
            ),
            execution_nature=ExecutionNature.AUTO,
            models=models_config,
            prompt_strategy=prompt_strategy.get_config(),
        )

        instance = cls(configuration)
        instance._agent_data = fields
        return instance


def get_os_info() -> str:
    os_name = platform.system()
    os_info = (
        platform.platform(terse=True)
        if os_name != "Linux"
        else distro.name(pretty=True)
    )
    return os_info
