from __future__ import annotations

import contextlib
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union
from superpilot.core.configuration import SystemSettings, Configurable
import yaml


class Config(SystemSettings, arbitrary_types_allowed=True):
    name: str = "Superpilot configuration"
    description: str = "Default configuration for the Superpilot application."
    ########################
    # Application Settings #
    ########################
    debug_mode: bool = False

    # Google
    google_api_key: Optional[str] = None
    google_custom_search_engine_id: Optional[str] = None
    # Huggingface
    huggingface_api_token: Optional[str] = None
    # Stable Diffusion
    sd_webui_auth: Optional[str] = None
    # SerpAPI
    serp_api_key: Optional[str] = None


class ConfigBuilder(Configurable[Config]):
    default_settings = Config()

    @classmethod
    def build_config_from_env(cls, workdir: Path = None) -> Config:
        config_dict_without_none_values = cls.load_env(workdir)

        config = cls.build_environment_configuration(config_dict_without_none_values)

        # Set secondary config variables (that depend on other config variables)

        # config.plugins_config = PluginsConfig.load_config(
        #     config.workdir / config.plugins_config_file,
        #     config.plugins_denylist,
        #     config.plugins_allowlist,
        # )

        return config

    @classmethod
    def load_env(cls, workdir):
        """Initialize the Config class"""
        config_dict = {
            "debug_mode": os.getenv("DEBUG_MODE", "False") == "True",
            "github_api_key": os.getenv("GITHUB_API_KEY"),
            "github_username": os.getenv("GITHUB_USERNAME"),
            "google_api_key": os.getenv("GOOGLE_API_KEY"),
            "serp_api_key": os.getenv("SERP_API_KEY"),
            "google_custom_search_engine_id": os.getenv("CUSTOM_SEARCH_ENGINE_ID"),
        }

        config_dict_without_none_values = {
            k: v for k, v in config_dict.items() if v is not None
        }
        return config_dict_without_none_values

