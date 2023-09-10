# flake8: noqa
import os
import sys
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from superpilot.examples.executor import (
    StableDiffusionPromptExecutor,
    MidjourneyPromptPromptExecutor,
    StableDiffusionImageExecutor,
)

sd_prompt = StableDiffusionPromptExecutor()
print("\n", "*" * 32, "Running StableDiffusionPromptExecutor", "*" * 32, "\n\n")
res = asyncio.run(sd_prompt.run("a photo of a cat"))
print(res.content)


sd_prompt = MidjourneyPromptPromptExecutor()
print("\n", "*" * 32, "Running MidjourneyPromptPromptExecutor", "*" * 32, "\n\n")
res = asyncio.run(sd_prompt.run("a photo of a cat"))
print(res.content)


sd_prompt = StableDiffusionImageExecutor()
from PIL import Image

print("\n", "*" * 32, "Running StableDiffusionImageExecutor", "*" * 32, "\n\n")
context = asyncio.run(sd_prompt.run("a photo of a cat"))
for item in context.items:
    print(item.description)
    Image.open(item.file_path).show()
