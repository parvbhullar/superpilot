from dataclasses import dataclass
import logging
from superpilot.core.ability.base import Ability, AbilityConfiguration, AbilityException
from superpilot.core.configuration import Config
from superpilot.core.environment import Environment
from superpilot.core.context.schema import Context
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.planning.base import PromptStrategy


class DefaultAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.DefaultAbility",
        ),
        packages_required=[],
        workspace_required=False,
    )

    def __init__(
        self,
        environment: Environment,
        configuration: AbilityConfiguration = default_configuration,
        prompt_strategy: PromptStrategy = None,
    ):
        self._logger: logging.Logger = environment.get("logger")
        self._configuration = configuration
        self._env_config: Config = environment.get("env_config")

    @classmethod
    def description(cls) -> str:
        return "default to call, summarises the task completion"

    @classmethod
    def arguments(cls) -> dict:
        return {
            "task_summary": {
                "type": "string",
                "description": "verbose completion summary of the task",
            }
        }

    async def __call__(self, task_summary: str = "", **kwargs):
        callback = kwargs.get("callback")
        self._summary = task_summary
        print('callback', callback)
        if callback:
            print("DefaultAbility", kwargs)
            await callback.on_info(message=task_summary, **kwargs)
        return task_summary


@dataclass
class ScheduleMeetingAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.ScheduleMeetingAbility",
        ),
        packages_required=[],
        workspace_required=False,
    )

    def __init__(
        self,
        environment: Environment,
        configuration: AbilityConfiguration = default_configuration,
    ):
        self._logger: logging.Logger = environment.get("logger")
        self._configuration = configuration

    @classmethod
    def description(cls) -> str:
        return "Schedule a meeting."

    @classmethod
    def arguments(cls) -> dict:
        return {
            "date": {"type": "string", "description": "Date of the meeting (YYYY-MM-DD)."},
            "time": {"type": "string", "description": "Time of the meeting (HH:MM)."},
            "participants": {"type": "list", "description": "List of participant emails."},
        }

    async def __call__(self, date: str, time: str, participants: list, **kwargs):
        message = f"Meeting scheduled on {date} at {time} with participants {', '.join(participants)}."
        callback = kwargs.get("callback")
        if callback:
            thread_id = kwargs.get("thread_id")
            await callback.on_info(thread_id, message)
        return Context.factory().add_content(message)


@dataclass
class CreateTaskAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.CreateTaskAbility",
        ),
        packages_required=[],
        workspace_required=False,
    )

    def __init__(
        self,
        environment: Environment,
        configuration: AbilityConfiguration = default_configuration,
    ):
        self._logger: logging.Logger = environment.get("logger")
        self._configuration = configuration

    @classmethod
    def description(cls) -> str:
        return "Create a task from email content."

    @classmethod
    def arguments(cls) -> dict:
        return {
            "task_description": {"type": "string", "description": "Description of the task."},
            "deadline": {"type": "string", "description": "Deadline for the task (YYYY-MM-DD)."},
        }

    async def __call__(self, task_description: str, deadline: str, **kwargs):
        message = f"Task created: '{task_description}' with deadline {deadline}."
        callback = kwargs.get("callback")
        if callback:
            thread_id = kwargs.get("thread_id")
            await callback.on_info(thread_id, message)
        return Context.factory().add_content(message)


@dataclass
class SummarizeEmailAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.SummarizeEmailAbility",
        ),
        packages_required=[],
        workspace_required=False,
    )

    def __init__(
        self,
        environment: Environment,
        configuration: AbilityConfiguration = default_configuration,
    ):
        self._logger: logging.Logger = environment.get("logger")
        self._configuration = configuration

    @classmethod
    def description(cls) -> str:
        return "Summarize email content."

    @classmethod
    def arguments(cls) -> dict:
        return {
            "email_content": {"type": "string", "description": "Content of the email."},
        }

    async def __call__(self, email_content: str, **kwargs):
        # Example of a placeholder summarization
        summary = email_content[:100] + "..." if len(email_content) > 100 else email_content
        message = f"Summary: {summary}"
        callback = kwargs.get("callback")
        if callback:
            thread_id = kwargs.get("thread_id")
            await callback.on_info(thread_id, message)
        return Context.factory().add_content(message)


@dataclass
class ExtractEntitiesAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.ExtractEntitiesAbility",
        ),
        packages_required=[],
        workspace_required=False,
    )

    def __init__(
        self,
        environment: Environment,
        configuration: AbilityConfiguration = default_configuration,
    ):
        self._logger: logging.Logger = environment.get("logger")
        self._configuration = configuration

    @classmethod
    def description(cls) -> str:
        return "Extract entities like dates, names, and numbers from email content."

    @classmethod
    def arguments(cls) -> dict:
        return {
            "email_content": {"type": "string", "description": "Content of the email."},
        }

    async def __call__(self, email_content: str, **kwargs):
        # Placeholder: Replace with actual entity extraction logic
        entities = {"dates": ["2024-12-03"], "names": ["John Doe"], "numbers": ["12345"]}
        message = f"Extracted entities: {entities}"
        callback = kwargs.get("callback")
        if callback:
            thread_id = kwargs.get("thread_id")
            await callback.on_info(thread_id, message)
        return Context.factory().add_content(message)


@dataclass
class CreateReminderAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.CreateReminderAbility",
        ),
        packages_required=[],
        workspace_required=False,
    )

    def __init__(
        self,
        environment: Environment,
        configuration: AbilityConfiguration = default_configuration,
    ):
        self._logger: logging.Logger = environment.get("logger")
        self._configuration = configuration

    @classmethod
    def description(cls) -> str:
        return "Create a reminder."

    @classmethod
    def arguments(cls) -> dict:
        return {
            "reminder_message": {"type": "string", "description": "The reminder message."},
            "reminder_time": {"type": "string", "description": "The time for the reminder (YYYY-MM-DD HH:MM)."},
        }

    async def __call__(self, reminder_message: str, reminder_time: str, **kwargs):
        message = f"Reminder set: '{reminder_message}' at {reminder_time}."
        callback = kwargs.get("callback")
        if callback:
            thread_id = kwargs.get("thread_id")
            await callback.on_info(thread_id, message)
        return Context.factory().add_content(message)
