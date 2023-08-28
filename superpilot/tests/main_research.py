import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
import click

from superpilot.core.pilot import AgentSettings, ResearchAgent
from superpilot.core.runner.client_lib.logging import get_client_logger
import asyncio


async def run_auto_gpt(user_configuration: dict):
    """Run the Superpilot CLI client."""

    client_logger = get_client_logger()
    client_logger.debug("Getting pilot settings")
    thread_id = "532955534064615681"

    pilot_workspace = (
        user_configuration.get("workspace", {}).get("configuration", {}).get("root", "")
    )

    if not pilot_workspace:  # We don't have an pilot yet.
        #################
        # Bootstrapping #
        #################
        # Step 1. Collate the user's settings with the default system settings.
        pilot_settings: AgentSettings = ResearchAgent.compile_settings(
            client_logger,
            user_configuration,
        )

        # Step 2. Get a name and goals for the pilot.
        # First we need to figure out what the user wants to do with the pilot.
        # We'll do this by asking the user for a prompt.
        # user_objective = click.prompt("What do you want Superpilot to do?")
        user_objective = 'research on what is GST'
        # Ask a language model to determine a name and goals for a suitable pilot.
        name_and_goals = await ResearchAgent.determine_pilot_name_and_goals(
            user_objective,
            pilot_settings,
            client_logger,
        )
        print(parse_pilot_name_and_goals(name_and_goals))
        # Finally, update the pilot settings with the name and goals.
        pilot_settings.update_pilot_name_and_goals(name_and_goals)

        # Step 3. Provision the pilot.
        # ResearchAgent.provision_pilot(pilot_settings, client_logger)
        ResearchAgent.provision_pilot_goal(
            user_objective, thread_id, pilot_settings, client_logger
        )
        print("pilot is provisioned")

    # launch pilot interaction loop
    pilot = ResearchAgent.from_goal(
        user_objective,
        thread_id,
        client_logger,
    )
    print("pilot is loaded")

    plan = await pilot.build_initial_plan()
    print(parse_pilot_plan(plan))

    while True:
        current_task, next_ability = await pilot.determine_next_ability(plan)
        print(parse_next_ability(current_task, next_ability))
        user_input = click.prompt(
            "Should the pilot proceed with this ability?",
            default="y",
        )
        if not next_ability["next_ability"]:
            print("Agent is done!", "No Next Ability Found")
            break
        ability_result = await pilot.execute_next_ability(user_input)
        print(parse_ability_result(ability_result))


def parse_pilot_name_and_goals(name_and_goals: dict) -> str:
    parsed_response = f"Agent Name: {name_and_goals['pilot_name']}\n"
    parsed_response += f"Agent Role: {name_and_goals['pilot_role']}\n"
    parsed_response += "Agent Goals:\n"
    for i, goal in enumerate(name_and_goals["pilot_goals"]):
        parsed_response += f"{i+1}. {goal}\n"
    return parsed_response


def parse_pilot_plan(plan: dict) -> str:
    parsed_response = f"Agent Plan:\n"
    for i, task in enumerate(plan["task_list"]):
        parsed_response += f"{i+1}. {task['objective']}\n"
        parsed_response += f"Task type: {task['type']}  "
        parsed_response += f"Priority: {task['priority']}\n"
        parsed_response += f"Ready Criteria:\n"
        for j, criteria in enumerate(task["ready_criteria"]):
            parsed_response += f"    {j+1}. {criteria}\n"
        parsed_response += f"Acceptance Criteria:\n"
        for j, criteria in enumerate(task["acceptance_criteria"]):
            parsed_response += f"    {j+1}. {criteria}\n"
        parsed_response += "\n"

    return parsed_response


def parse_next_ability(current_task, next_ability: dict) -> str:
    parsed_response = f"Current Task: {current_task.objective}\n"
    ability_args = ", ".join(
        f"{k}={v}" for k, v in next_ability["ability_arguments"].items()
    )
    parsed_response += f"Next Ability: {next_ability['next_ability']}({ability_args})\n"
    parsed_response += f"Motivation: {next_ability['motivation']}\n"
    parsed_response += f"Self-criticism: {next_ability['self_criticism']}\n"
    parsed_response += f"Reasoning: {next_ability['reasoning']}\n"
    return parsed_response


def parse_ability_result(ability_result) -> str:
    parsed_response = f"Ability: {ability_result['ability_name']}\n"
    parsed_response += f"Ability Arguments: {ability_result['ability_args']}\n"
    parsed_response = f"Ability Result: {ability_result['success']}\n"
    parsed_response += f"Message: {ability_result['message']}\n"
    parsed_response += f"Data: {ability_result['knowledge']}\n"
    return parsed_response


if __name__ == "__main__":
    asyncio.run(run_auto_gpt({}))
