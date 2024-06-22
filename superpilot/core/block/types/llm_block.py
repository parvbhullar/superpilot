import logging
import os

from superpilot.core.block.base import Block, BlockConfiguration
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.workspace import Workspace


class LLMBlock(Block):
    default_configuration = BlockConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.LLMBlock",
        ),
        block_type="llm",
        metadata={
            "name": "llm",
            "description": "A block that uses a language model to generate text.",
            "config": {
                "model_name": "gpt-3.5-turbo",
                "model_temp": "0.5",
                "system_prompt": "Write a story about a dragon based on given keywords",
            }
        },
        input_schema={
            "genre": {
                "type": "string",
                "description": "The genre of the story.",
            },
            "keywords": {
                "type": "string",
                "description": "Temp of the model to use.",
            },
        },
        output_schema={
            "output": {
                "type": "string",
                "description": "The output of the block.",
            },
        },
        body="",
    )

    def __init__(
        self,
        logger: logging.Logger,
        workspace: Workspace,
    ):
        self._logger = logger
        self._workspace = workspace

    @property
    def description(self) -> str:
        return "LLM block."

    @property
    def config(self) -> dict:
        return {
            "model_name": {
                "type": "string",
                "description": "The name of the model to use.",
            },
            "model_temp": {
                "type": "string",
                "description": "Temp of the model to use.",
            },
            "system_prompt": {
                "type": "string",
                "description": "The system prompt to use.",
            },
        }

    def __call__(self, args: dict) -> dict:
        pass