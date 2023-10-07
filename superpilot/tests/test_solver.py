# flake8: noqa
import os
import sys
import asyncio
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.examples.ed_tech.question_executor import QuestionExecutor
from superpilot.framework.tools.latex import latex_to_text
import pandas as pd


def solve_question(image_path):
    t1 = time.time()
    executor = QuestionExecutor()
    print("\n", "*" * 32, "Running QuestionExecutor", "*" * 32, "\n\n")
    res = asyncio.run(executor.run(image_path))
    print(res)
    # print(res.content.get("status"))
    t2 = time.time()
    print("Time Taken", round(t2 - t1, 2), "seconds")


if __name__ == "__main__":
    path = '/Users/parvbhullar/Drives/Vault/Projects/Unpod/superpilot/superpilot/docs/WhatsApp Image 2023-10-03 at 8.31.50 PM.jpeg'
    path = '/Users/parvbhullar/Drives/Vault/Projects/Unpod/superpilot/superpilot/docs/WhatsApp Image 2023-10-03 at 8.31.50 PM.jpeg'
    solve_question(path)