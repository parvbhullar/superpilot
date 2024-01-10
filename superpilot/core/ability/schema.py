from typing import Dict, Any
from pydantic import ConfigDict, BaseModel
from superpilot.core.context.schema import Context


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
    knowledge: Context = None
    # model_config = ConfigDict(arbitrary_types_allowed=True)

    class Config:
        arbitrary_types_allowed = True

    def add_result(self, result: Any):
        # print("Ability Knowledge", knowledge)
        self.result = result

    def summary(self):
        return self.__str__()

    def __str__(self):
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


