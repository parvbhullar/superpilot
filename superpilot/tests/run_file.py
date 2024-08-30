from concurrent import futures
import os
import sys
import asyncio
import time
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from superpilot.examples.executor import QuestionExtractorExecutor
from superpilot.superpilot.mapping_csv.extractcsv.check_file import checkMerge

import pandas as pd

run_timestamp = time.strftime("%Y%m%d-%H%M%S")

columns = [
    "Original Keyword",
    "question",
    "options",
    "question_status",
    "subject",
    "question_type",
    "total_cost($)",
]


def process_single_file(chunk, index):
    t1 = time.time()
    sd_prompt = QuestionExtractorExecutor()
    print(
        "\n", "*" * 32, "Running QuestionExtractorExecutor " + index, "*" * 32, "\n\n"
    )
    try:
        success, error = asyncio.run(sd_prompt.run_list(chunk))
    except Exception as Ex:
        traceback.print_exc()
        return [], []
    t2 = time.time()
    print("Time Taken", round(t2 - t1, 2), "seconds")
    if len(success) > 0:
        success_df = pd.DataFrame(success)
        success_df = success_df.reindex(columns=columns)
        success_df.to_csv(
            "latex_response_" + run_timestamp + ".csv",
            mode="a+",
            index=False,
            header=(not os.path.exists("latex_response_" + run_timestamp + ".csv")),
        )
    if len(error) > 0:
        error_df = pd.DataFrame(error)
        error_df.to_csv(
            "latex_error_" + run_timestamp + ".csv",
            mode="a+",
            index=False,
            header=(not os.path.exists("latex_error_" + run_timestamp + ".csv")),
        )


def run_file_with_search(file_location):
    data_df = pd.read_excel(file_location, sheet_name="WorkingSheet", header=1)
    data_df = data_df.reindex(columns=["Original Keyword"])
    last_index_name = file_location.split("/")[-1]
    last_index_name = os.path.splitext(last_index_name)[0]
    last_index_name = last_index_name.replace(" ", "_")
    last_index_name = f"last_index_{last_index_name}.txt"
    os.path.exists(last_index_name) or open(last_index_name, "w+").write("")
    last_index = open(last_index_name, "r+").read()
    if last_index == "":
        last_index = 0
    else:
        last_index = int(last_index)

    file_size = 50

    max_workers = 10
    total_data = len(data_df)
    if total_data <= last_index:
        print("No Processing Done", file_location)
        return True

    futures_tasks = []
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(max_workers):
            if total_data <= last_index:
                break
            chunk = data_df[last_index : last_index + file_size]
            last_index += len(chunk)
            futures_tasks.append(
                executor.submit(
                    process_single_file, chunk.to_dict(orient="records"), str(i)
                )
            )
    futures.wait(futures_tasks)
    with open(last_index_name, "w+") as f:
        f.write(str(last_index))
    return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Please provide file location")
        sys.exit(1)
    file_location = sys.argv[1]
    # file_location = "AI Answer 5M scraping semrush 2023-09-27 CB5.xlsx"
    while True:
        cycle_count = 1
        res = run_file_with_search(file_location)
        if res:
            break
        print("Sleeping for 5 seconds", cycle_count)
        cycle_count += 1
        time.sleep(5)

    checkMerge(
        ["latex_response_" + run_timestamp + ".csv"], file_location, run_timestamp
    )
