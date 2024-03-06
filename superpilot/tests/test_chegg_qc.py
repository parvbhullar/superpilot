import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.examples.executor.chegg_qc import CheggQCExecutor
from superpilot.examples.solution_qc.executor import QuestionAnalysisExecutor


input_file = "sample_questions-small.xlsx"
output_file = "sample_questions_output_scrap.xlsx"
executor = CheggQCExecutor()
response = asyncio.run(executor.run(input_file, output_file))

print("Run CheggQCExecutor")
executor_analsyis = QuestionAnalysisExecutor()
output_file_analysis = "sample_questions_output_qc.xlsx"
response = asyncio.run(
    executor_analsyis.run(input_file=output_file, output_file=output_file_analysis)
)
print(response)
