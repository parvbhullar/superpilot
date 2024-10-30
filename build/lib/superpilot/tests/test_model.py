# flake8: noqa
import os
import sys
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.examples.executor.model import ModelPilotExecutor

if __name__ == "__main__":
    pilot = ModelPilotExecutor("openai", "gpt-3.5-turbo-0613")
    task = "Provide the curret news related to indian stock market"
    res = asyncio.run(pilot.run(task))
    print(res.content)
