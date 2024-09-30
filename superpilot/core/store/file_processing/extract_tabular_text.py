import json

from super_store.parser import FileParser
from super_store.schema import SchemaCreator
from superpilot.core.store.file_processing.extract_file_text import _extract_unpod_metadata
import asyncio


def record_to_text(row, **metadata):
    content = ""
    for i, (k, v) in enumerate(row.items()):
        # TODO change this to more human readable format
        try:
            content += f"{k}:{v}\n"
        except Exception as e:
            continue
    return content, {**row, **metadata}


def read_tabular_file(
    file_name: str,
    errors: str = "replace",
    ignore_unpod_metadata: bool = True,
):
    parser = FileParser()
    processed_data = asyncio.run(parser.read_data_file(file_name, None, load_only=True))
    is_success = processed_data.get("success", False)
    if not is_success:
        return processed_data
    data = processed_data.get("data", {}).get("docs", [])
    schema = processed_data.get("data", {}).get("columns", {})

    schema_creator = SchemaCreator()
    json_schema = schema_creator.create_schema(schema)
    # documents = []
    for row in data:
        document, metadata = record_to_text(row, schema=json.dumps(json_schema))
        # documents.append(document)
    # return documents, metadata
        yield document, metadata
