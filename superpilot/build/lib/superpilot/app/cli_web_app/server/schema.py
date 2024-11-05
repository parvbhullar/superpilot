from typing import Dict, List
from uuid import UUID

from pydantic import BaseModel, validator


class AgentInfo(BaseModel):
    id: UUID = None
    objective: str = ""
    name: str = ""
    role: str = ""
    goals: List[str] = []


class AgentConfiguration(BaseModel):
    """Configuration for creation of a new pilot."""

    # We'll want to get this schema from the configuration, so it needs to be dynamic.
    user_configuration: dict
    pilot_goals: AgentInfo

    @validator("pilot_goals")
    def only_objective_or_name_role_goals(cls, pilot_goals):
        goals_specification = [pilot_goals.name, pilot_goals.role, pilot_goals.goals]
        if pilot_goals.objective and any(goals_specification):
            raise ValueError("Cannot specify both objective and name, role, or goals")
        if not pilot_goals.objective and not all(goals_specification):
            raise ValueError("Must specify either objective or name, role, and goals")


class InteractRequestBody(BaseModel):
    user_input: str = ""


class InteractResponseBody(BaseModel):
    thoughts: Dict[str, str]  # TBD
    messages: List[str]  # for example
