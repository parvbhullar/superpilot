import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.examples.executor.chegg_qc import CheggQCExecutor

input_file = "test_sample.xlsx"
output_file = "test_sample_output.xlsx"
executor = CheggQCExecutor()
response = asyncio.run(executor.run(input_file, output_file))
print(response)
