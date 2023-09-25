"""This module contains functions to fix JSON strings generated by LLM models, such as ChatGPT, using the assistance
of the ChatGPT API or LLM models."""
from __future__ import annotations

import contextlib
import json
from typing import Any, Dict

from colorama import Fore
from regex import regex

from superpilot.core.configuration import Config
from superpilot.framework.helpers.json_utils.json_fix_general import correct_json
from superpilot.framework.llm import call_ai_function, create_chat_completion
from superpilot.framework.helpers.logs import logger
import openai

JSON_SCHEMA = """
{
    "command": {
        "name": "command name",
        "args": {
            "arg name": "value"
        }
    },
    "thoughts":
    {
        "text": "thought",
        "reasoning": "reasoning",
        "plan": "- short bulleted\n- list that conveys\n- long-term plan",
        "criticism": "constructive self-criticism",
        "speak": "thoughts summary to say to user"
    }
}
"""

CFG = Config()


def auto_fix_json(json_string: str, schema: str) -> str:
    """Fix the given JSON string to make it parseable and fully compliant with
        the provided schema using GPT-3.

    Args:
        json_string (str): The JSON string to fix.
        schema (str): The schema to use to fix the JSON.
    Returns:
        str: The fixed JSON string.
    """
    # OLD Implementation:
    # Try to fix the JSON using GPT:
    function_string = "def fix_json(json_string: str, schema:str=None) -> str:"
    args = [f"'''{json_string}'''", f"'''{schema}'''"]
    description_string = (
        "This function takes a JSON string and ensures that it"
        " is parseable and fully compliant with the provided schema. If an object"
        " or field specified in the schema isn't contained within the correct JSON,"
        " it is omitted. The function also escapes any double quotes within JSON"
        " string values to ensure that they are valid. If the JSON string contains"
        " any None or NaN values, they are replaced with null before being parsed."
        " If the string is not parseable to json, then try to pass whole string as suitable arguments to the function."
    )

    # If it doesn't already start with a "`", add one:
    if not json_string.startswith("`"):
        json_string = "```json\n" + json_string + "\n```"
    # result_string = call_ai_function(
    #     function_string, args, description_string, model=CFG.fast_llm_model
    # )

    system_prompt = f"Fix the following string to make it parseable and fully compliant with the provided schema:\n{schema}\n remove any mentions of function name in arguments.\n"
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": f"JSON string:\n{json_string}\n\n",
        },
    ]
    completion = openai.ChatCompletion.create(
        model=CFG.fast_llm_model,
        temperature=0,
        functions=[schema],
        function_call={"name": schema["name"]},
        messages=messages,
        max_tokens=CFG.fast_token_limit,
    )
    message = completion.choices[0].message
    try:
        function_call = message["function_call"]

        arguments = function_call["arguments"]
        if isinstance(arguments, (str, bytes, bytearray)):
            arguments = json.loads(arguments)
        function_call["arguments"] = arguments

        result_string = json.dumps(function_call)

        logger.debug("------------ JSON FIX ATTEMPT ---------------")
        # logger.debug(f"Original JSON: {json_string}")
        # logger.debug("-----------")
        logger.debug(f"Fixed JSON: {result_string}")
        logger.debug("----------- END OF FIX ATTEMPT ----------------")

        json.loads(result_string)  # just check the validity
        return result_string
    except json.JSONDecodeError:  # noqa: E722
        # Get the call stack:
        # import traceback
        # call_stack = traceback.format_exc()
        # print(f"Failed to fix JSON: '{json_string}' "+call_stack)
        return "failed"


def fix_json_using_multiple_techniques(assistant_reply: str, schema: dict) -> Dict[Any, Any]:
    """Fix the given JSON string to make it parseable and fully compliant with two techniques.

    Args:
        json_string (str): The JSON string to fix.

    Returns:
        str: The fixed JSON string.
    """
    assistant_reply = assistant_reply.strip()
    if assistant_reply.startswith("```json"):
        assistant_reply = assistant_reply[7:]
    if assistant_reply.endswith("```"):
        assistant_reply = assistant_reply[:-3]
    try:
        return json.loads(assistant_reply)  # just check the validity
    except json.JSONDecodeError:  # noqa: E722
        pass

    if assistant_reply.startswith("json "):
        assistant_reply = assistant_reply[5:]
        assistant_reply = assistant_reply.strip()
    try:
        return json.loads(assistant_reply)  # just check the validity
    except json.JSONDecodeError:  # noqa: E722
        pass

    # Parse and print Assistant response
    assistant_reply_json = fix_and_parse_json(assistant_reply, schema=schema)
    logger.debug("Assistant reply JSON: %s", str(assistant_reply_json))
    if assistant_reply_json == {}:
        assistant_reply_json = attempt_to_fix_json_by_finding_outermost_brackets(
            assistant_reply
        )

    logger.debug("Assistant reply JSON 2: %s", str(assistant_reply_json))
    if assistant_reply_json != {}:
        return assistant_reply_json

    logger.error(
        "Error: The following AI output couldn't be converted to a JSON:\n",
        assistant_reply,
    )
    if CFG.speak_mode:
        say_text("I have received an invalid JSON response from the OpenAI API.")

    return {}


def fix_and_parse_json(
    json_to_load: str, try_to_fix_with_gpt: bool = True, schema: dict = None
) -> Dict[Any, Any]:
    """Fix and parse JSON string

    Args:
        json_to_load (str): The JSON string.
        try_to_fix_with_gpt (bool, optional): Try to fix the JSON with GPT.
            Defaults to True.
        schema (dict, optional): The schema to use to fix the JSON.

    Returns:
        str or Dict[Any, Any]: The parsed JSON.
    """

    with contextlib.suppress(json.JSONDecodeError):
        json_to_load = json_to_load.replace("\t", "")
        return json.loads(json_to_load)

    with contextlib.suppress(json.JSONDecodeError):
        json_to_load = correct_json(json_to_load)
        return json.loads(json_to_load)
    # Let's do something manually:
    # sometimes GPT responds with something BEFORE the braces:
    # "I'm sorry, I don't understand. Please try again."
    # {"text": "I'm sorry, I don't understand. Please try again.",
    #  "confidence": 0.0}
    # So let's try to find the first brace and then parse the rest
    #  of the string
    try:
        brace_index = json_to_load.index("{")
        maybe_fixed_json = json_to_load[brace_index:]
        last_brace_index = maybe_fixed_json.rindex("}")
        maybe_fixed_json = maybe_fixed_json[: last_brace_index + 1]
        return json.loads(maybe_fixed_json)
    except (json.JSONDecodeError, ValueError) as e:
        return try_ai_fix(try_to_fix_with_gpt, e, json_to_load, schema)


def try_ai_fix(
    try_to_fix_with_gpt: bool, exception: Exception, json_to_load: str, schema: dict = None
) -> Dict[Any, Any]:
    """Try to fix the JSON with the AI

    Args:
        try_to_fix_with_gpt (bool): Whether to try to fix the JSON with the AI.
        exception (Exception): The exception that was raised.
        json_to_load (str): The JSON string to load.
        schema (str, optional): The schema to use. Defaults to None.

    Raises:
        exception: If try_to_fix_with_gpt is False.

    Returns:
        str or Dict[Any, Any]: The JSON string or dictionary.
    """
    if not try_to_fix_with_gpt:
        raise exception
    if CFG.debug_mode:
        logger.warn(
            "Warning: Failed to parse AI output, attempting to fix."
            "\n If you see this warning frequently, it's likely that"
            " your prompt is confusing the AI. Try changing it up"
            " slightly."
        )
    # Now try to fix this up using the ai_functions
    ai_fixed_json = auto_fix_json(json_to_load, JSON_SCHEMA if schema is None else schema)

    if ai_fixed_json != "failed":
        return json.loads(ai_fixed_json)
    # This allows the AI to react to the error message,
    #   which usually results in it correcting its ways.
    # logger.error("Failed to fix AI output, telling the AI.")
    return {}


def attempt_to_fix_json_by_finding_outermost_brackets(json_string: str):
    if CFG.speak_mode and CFG.debug_mode:
        say_text(
            "I have received an invalid JSON response from the OpenAI API. "
            "Trying to fix it now."
        )
        logger.error("Attempting to fix JSON by finding outermost brackets\n")

    try:
        json_pattern = regex.compile(r"\{(?:[^{}]|(?R))*\}")
        json_match = json_pattern.search(json_string)

        if json_match:
            # Extract the valid JSON object from the string
            json_string = json_match.group(0)
            logger.typewriter_log(
                title="Apparently json was fixed.", title_color=Fore.GREEN
            )
            if CFG.speak_mode and CFG.debug_mode:
                say_text("Apparently json was fixed.")
        else:
            return {}

    except (json.JSONDecodeError, ValueError):
        if CFG.debug_mode:
            logger.error(f"Error: Invalid JSON: {json_string}\n")
        if CFG.speak_mode:
            say_text("Didn't work. I will have to ignore this response then.")
        logger.error("Error: Invalid JSON, setting it to empty JSON now.\n")
        json_string = {}

    return fix_and_parse_json(json_string)
