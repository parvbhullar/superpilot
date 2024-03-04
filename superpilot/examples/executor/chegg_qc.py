from superpilot.examples.executor.base import BaseExecutor
from superpilot.examples.solution_qc.chegg_scrap import process_chegg_file


class CheggQCExecutor(BaseExecutor):
    def __init__(self, **kwargs):  # type: ignore
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def run(self, input_file, output_file):
        file_path, count, total_count = process_chegg_file(input_file, output_file)
        file_name = file_path.split("/")[-1]
        print(file_path, count)
        return {
            "message": f"file successfully processed",
            "file_name": file_name,
            "processed_count": count,
            "total_count": total_count,
        }
