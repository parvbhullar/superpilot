from typing import Dict

from superpilot.pilot.core.schema import GoalSchema
from superpilot.pilot.core.store import GoalStore


def config_to_goal(user_objective: str, thread_id: str, settings_json: Dict):
    name = settings_json.get("pilot", {}).get("name")
    goals = settings_json.get("pilot", {}).get("configuration", {}).get("goals", [])
    tasks = []
    for index, task in enumerate(goals):
        tasks.append({"task_id": index + 1, "task": task, 'result': ''})
    return GoalSchema(
        goal=user_objective,
        thread_id=thread_id,
        tasks=tasks,
        pilot_handle=name,
        settings_json=settings_json,
    )


def save_goal(goal: GoalSchema):
    goal_store = GoalStore.get_goal_by(goal)
    return goal_store


def fetch_goal(user_objective: str, thread_id: str, config_name: str):
    goal = GoalStore.find_one(
        goal=user_objective, thread_id=thread_id, pilot_handle=config_name
    )
    return goal or {}
