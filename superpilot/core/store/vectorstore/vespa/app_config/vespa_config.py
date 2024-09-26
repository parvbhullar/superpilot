
import requests
from dotenv import load_dotenv
import os

def load_env(cls, workdir):
        """Initialize the Config class"""
        config_dict = {
            "debug_mode": os.getenv("DEBUG_MODE", "False") == "True",
            "github_api_key": os.getenv("GITHUB_API_KEY"),
            "github_username": os.getenv("GITHUB_USERNAME"),
            "google_api_key": os.getenv("GOOGLE_API_KEY"),
            "serp_api_key": os.getenv("SERP_API_KEY"),
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "google_custom_search_engine_id": os.getenv("CUSTOM_SEARCH_ENGINE_ID"),
            "fast_llm_model": os.getenv("FAST_LLM_MODEL"),
            "smart_llm_model": os.getenv("SMART_LLM_MODEL"),
            "stability_api_key": os.getenv("STABILITY_API_KEY"),
            "stability_engine_id": os.getenv("STABILITY_ENGINE_ID"),
            "clipdrop_api_key": os.getenv("CLIPDROP_API_KEY"),
            "web_proxy": os.getenv("WEB_PROXY", "").split(","),
            "selenium_browser_type": os.getenv("SELENIUM_BROWSER_TYPE", "chrome"),
            "scraperapi_api_key": os.getenv("SCRAPERAPI_API_KEY"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "together_api_key": os.getenv("TOGETHER_API_KEY"),
            "deepinfra_api_key": os.getenv("DEEPINFRA_API_KEY"),
        }

        config_dict_without_none_values = {
            k: v for k, v in config_dict.items() if v is not None
        }
        return config_dict_without_none_values