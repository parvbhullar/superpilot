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
neg_content = """
A landscape space that is dominated by white, grey, blue, and green colors, suggest which of the following sensory responses of human actions?  A) Gay, lively  B) Relaxing, stable  C) Frightening, inhibiting  D) Regressive, detached
"""

ques = """
The ______exercises all authority over the establishment of education, experience, and other criteria for licensing, certification, and re-certification of qualified appraisers."""

ques1 = """
A technician wants to share a printer on the network but according to the company policy, no PC should have a directly connected printer. Which device would the technician need?"""

ques2 = """
Which of the following modalities has the potential to be used effectively in every phase of the OPT model? Terra-Core Cable machines TRX Rip Trainer Suspended bodyweight training"""

ques3 = """
Movie Recommendation systems are an example of: 1. Classification 2. Clustering 3. Reinforcement Learning 4. Regression Options: B. A. 2 Only C. 1 and 2 D. 1 and 3 E. 2 and 3 F. 1, 2 and 3 H. 1, 2, 3 and 4
"""

ques4 = """
24. End-user data is . a. knowledge about the end users b. raw facts of interest to the end user c. information about a specific subject d. accurate, relevant and timely information
"""

def fix_question(content):
    t1 = time.time()
    sd_prompt = QuestionIdentifierPromptExecutor()
    print("\n", "*" * 32, "Running QuestionIdentifierPromptExecutor", "*" * 32, "\n\n")
    res = asyncio.run(sd_prompt.run(content))
    print(res)
    # print(res.content.get("status"))
    t2 = time.time()
    print("Time Taken", round(t2 - t1, 2), "seconds")


# fix_question(ques4)


def run_file():
    data_df = pd.read_excel(
        "/Users/parvbhullar/Drives/Vault/Projects/Unpod/superpilot/superpilot/docs/QuestionsData1.xlsx",
        sheet_name="Sheet1"
    )
    smaple_data = data_df[10:50].reindex(columns=["Original keyword"])
    print(smaple_data.shape)
    t1 = time.time()
    sd_prompt = QuestionIdentifierPromptExecutor()
    print("\n", "*" * 32, "Running QuestionIdentifierPromptExecutor", "*" * 32, "\n\n")
    res = asyncio.run(sd_prompt.run_list(smaple_data.to_dict("records")))
    t2 = time.time()
    print("Time Taken", round(t2 - t1, 2), "seconds")
    final_df = pd.DataFrame(res)
    final_df.to_excel("final_response.xlsx")


run_file()
