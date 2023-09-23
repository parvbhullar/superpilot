# flake8: noqa
import os
import sys
import asyncio
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from superpilot.examples.executor import (
    StableDiffusionPromptExecutor,
    MidjourneyPromptPromptExecutor,
    StableDiffusionImageExecutor,
    QuestionIdentifierPromptExecutor,
    ClipDropImageExecutor,
)

import pandas as pd

# sd_prompt = StableDiffusionPromptExecutor()
# print("\n", "*" * 32, "Running StableDiffusionPromptExecutor", "*" * 32, "\n\n")
# res = asyncio.run(sd_prompt.run("a photo of a cat"))
# print(res.content)


# sd_prompt = MidjourneyPromptPromptExecutor()
# print("\n", "*" * 32, "Running MidjourneyPromptPromptExecutor", "*" * 32, "\n\n")
# res = asyncio.run(sd_prompt.run("a photo of a cat"))
# print(res.content)


# sd_prompt = StableDiffusionImageExecutor()
# from PIL import Image

# print("\n", "*" * 32, "Running StableDiffusionImageExecutor", "*" * 32, "\n\n")
# context = asyncio.run(sd_prompt.run("a photo of a cat"))
# for item in context.items:
#     print(item.description)
#     Image.open(item.file_path).show()

# cd_prompt = ClipDropImageExecutor()
# from PIL import Image

# print("\n", "*" * 32, "Running ClipDropImageExecutor", "*" * 32, "\n\n")
# context = asyncio.run(cd_prompt.run("A Man drinking beer & playing with dog"))
# for item in context.items:
#     print(item.description)
#     Image.open(item.file_path).show()

# data_df = pd.read_excel("/home/dora/Downloads/Cloudbird Done Data.xlsx", sheet_name="9 sep")
content = """
A landscape space that is dominated by white, grey, blue, and green colors, suggest which of the following sensory responses of human actions?  A) Gay, lively  B) Relaxing, stable  C) Frightening, inhibiting  D) Regressive, detached
"""

# content = """
# Which of the following is not true regarding data mining? _______ A) It focuses on discovering useful information.  B) It can use machine learning techniques. C) It is one task within a process. D) It is a process from start to end."""
# t1 = time.time()
# sd_prompt = QuestionIdentifierPromptExecutor()
# print("\n", "*" * 32, "Running QuestionIdentifierPromptExecutor", "*" * 32, "\n\n")
# res = asyncio.run(sd_prompt.run(content))
# print(res.content.get("content"))
# print(res.content.get("status"))
# t2 = time.time()
# print("Time Taken", round(t2 - t1, 2), "seconds")


data_df = pd.read_excel(
    "/home/mastersindia/Documents/ML_Docs/Cloudbird Done Data.xlsx", sheet_name="9 sep"
)
smaple_data = data_df[:10].reindex(columns=["Original keyword"])
print(smaple_data.shape)
t1 = time.time()
sd_prompt = QuestionIdentifierPromptExecutor()
print("\n", "*" * 32, "Running QuestionIdentifierPromptExecutor", "*" * 32, "\n\n")

res = asyncio.run(sd_prompt.run_list(smaple_data.to_dict("records")))
t2 = time.time()
print("Time Taken", round(t2 - t1, 2), "seconds")
final_df = pd.DataFrame(res)
cols = ["Original keyword", "content", "status", "reason"]
headers = ["Original keyword", "Completed Version", "status", "reason"]
final_df = final_df.reindex(columns=cols)
final_df.to_excel("final_response.xlsx", header=headers, index=False)
