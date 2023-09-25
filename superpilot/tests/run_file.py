from concurrent import futures
import os
import sys
import asyncio
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from superpilot.examples.executor import QuestionExtractorExecutor

import pandas as pd

run_timestamp = time.strftime("%Y%m%d-%H%M%S")


def process_single_file(chunk, index):
    t1 = time.time()
    sd_prompt = QuestionExtractorExecutor()
    print(
        "\n", "*" * 32, "Running QuestionExtractorExecutor " + index, "*" * 32, "\n\n"
    )
    success, error = asyncio.run(sd_prompt.run_list(chunk))
    t2 = time.time()
    print("Time Taken", round(t2 - t1, 2), "seconds")
    if len(success) > 0:
        success_df = pd.DataFrame(success)
        success_df.to_csv(
            "latex_response_" + index + run_timestamp + ".csv", mode="a+", index=False
        )
    if len(error) > 0:
        error_df = pd.DataFrame(error)
        error_df.to_csv(
            "latex_error_" + index + run_timestamp + ".csv", mode="a+", index=False
        )


def run_file_with_search():
    file_location = ""
    data_df = pd.read_csv(file_location)
    data_df = data_df.reindex(columns=["Original Keyword"])
    last_index = open("last_index.txt", "r+").read()
    if last_index == "":
        last_index = 0
    else:
        last_index = int(last_index)

    file_size = 100
    max_workers = 10
    total_data = len(data_df)
    if total_data <= last_index:
        print("No Processing Done", file_location)
        return True

    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(max_workers):
            if total_data <= last_index:
                break
            chunk = data_df[last_index : last_index + file_size]
            last_index += file_size
            executor.submit(
                process_single_file, chunk.to_dict(orient="records"), str(i)
            )
    with open("last_index.txt", "w+") as f:
        f.write(str(last_index))


run_file_with_search()