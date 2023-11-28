from typing import Dict, Type, Any, Optional
from pydantic import BaseModel, create_model, root_validator, validator
from superpilot.core.context.schema import Context, Content


class AbilityAction(BaseModel):
    """The AbilityAction is a standard response struct for an ability."""
    task_id: str = ""
    thread_id: str = ""
    ability_name: str = ""
    ability_args: Dict[str, str] = {}
    success: bool = False
    executed: bool = False
    wait_for_user: bool = False
    message: str = ""
    knowledge: Context = None

    class Config:
        arbitrary_types_allowed = True

    def add_knowledge(self, knowledge: Context):
        # print("Ability Knowledge", knowledge)
        self.knowledge = knowledge

    def summary(self):
        # return self.knowledge.content

        kwargs = ", ".join(f"{k}={v}" for k, v in self.ability_args.items())
        return f"{self.ability_name}({kwargs}): {self.message}"



