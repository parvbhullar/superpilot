import ast
import json
from typing import List


def to_numbered_list(
    items: List[str], no_items_response: str = "", use_format=True, **template_args,
) -> str:
    if items:
        if not use_format:
            return "\n".join(
                f"{i+1}. {item}" for i, item in enumerate(items)
            )
        else:
            # no requirement to use format?
            return "\n".join(
                f"{i+1}. {item}" for i, item in enumerate(items)
            )
    else:
        return no_items_response


def json_loads(json_str: str):
    # TODO: this is a hack function for now. Trying to see what errors show up in testing.
    #   Can hopefully just replace with a call to ast.literal_eval (the function api still
    #   sometimes returns json strings with minor issues like trailing commas).
    try:
        return json.loads(json_str)
    except json.decoder.JSONDecodeError as e:
        try:
            print(f"json decode error {e}. trying literal eval")
            return ast.literal_eval(json_str)
        except Exception as ex:
            try:
                json_str = json_str.replace("'s", "")
                return ast.literal_eval(json_str)
            except Exception as ex2:
                raise ex2
            raise ex
            # breakpoint()
