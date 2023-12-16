from typing import Dict, Type, Any, Optional
from pydantic import BaseModel, create_model, root_validator, validator
from superpilot.core.context.schema import Context, Content


class AbilityAction(BaseModel):
    """The AbilityAction is a standard response struct for an ability."""
    thread_id: str = ""
    action_objective: str = ""
    ability_name: str = ""
    ability_args: Dict[str, str] = {}
    success: bool = False
    executed: bool = False
    wait_for_user: bool = False
    message: str = ""
    result: Context = None

    class Config:
        arbitrary_types_allowed = True

    def add_result(self, result: Context):
        # print("Ability Knowledge", knowledge)
        self.result = result

    def summary(self):
        # return self.knowledge.content
        kwargs = ", ".join(f"{k}={v}" for k, v in self.ability_args.items())
        # return f"{self.ability_name}({kwargs}): {self.message}"
        return (
            f"objective: {self.action_objective}\n"
            f"action:{self.ability_name}({kwargs})\n"
            "```\n"
            f"result:{self.message}\n"
            "```"
        )

    def get_memories(self):
        # print("get_memories", self.result.to_list())
        return self.result.to_list()


