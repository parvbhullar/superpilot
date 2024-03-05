import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.examples.executor.chegg_qc import CheggQCExecutor
from superpilot.examples.solution_qc.executor import QuestionAnalysisExecutor


input_file = "test_sample.xlsx"
output_file = "test_sample_output.xlsx"
executor = CheggQCExecutor()
response = asyncio.run(executor.run(input_file, output_file))
executor_analsyis = QuestionAnalysisExecutor()
output_file_analysis = "test_sample_analysis.xlsx"
response = asyncio.run(
    executor_analsyis.run(input_file=output_file, output_file=output_file_analysis)
)
print(response)
