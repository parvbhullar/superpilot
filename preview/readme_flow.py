"""Run the README quickstart: SimpleTaskPilot answering one query.

Mirrors superpilot/tests/test_readme.py (whose ModelProviderFactory import is
stale) without the unreachable code after its exit(0).

Usage: python preview/readme_flow.py ["Your query"]
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from superpilot.core.configuration import get_config
from superpilot.core.context.schema import Context
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIProvider,
)


async def main(query: str) -> None:
    config = get_config()
    open_ai_provider = OpenAIProvider.factory(config.openai_api_key)
    model_providers = {ModelProviderName.OPENAI: open_ai_provider}

    task_pilot = SimpleTaskPilot(model_providers=model_providers)
    print(f"Query: {query}")
    response = await task_pilot.execute(query, Context())
    print("Content:", response.content.get("content"))
    for highlight in response.content.get("highlights", []):
        print(" -", highlight)
    print("Model:", response.model_info.name)
    print("Tokens:", response.prompt_tokens_used, "+", response.completion_tokens_used)


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or "What is the weather in Mumbai"))
