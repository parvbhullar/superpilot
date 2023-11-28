import enum
from typing import List

from pydantic import BaseModel, Field

from superpilot.core.ability.schema import AbilityAction
from superpilot.core.resource.model_providers.schema import (
    LanguageModelFunction,
    LanguageModelMessage,
    LanguageModelProviderModelResponse,
)


class LanguageModelClassification(str, enum.Enum):
    """The LanguageModelClassification is a functional description of the model.

    This is used to determine what kind of model to use for a given prompt.
    Sometimes we prefer a faster or cheaper model to accomplish a task when
    possible.

    """

    FAST_MODEL: str = "fast_model"
    SMART_MODEL: str = "smart_model"


class LanguageModelPrompt(BaseModel):
    messages: List[LanguageModelMessage]
    functions: List[LanguageModelFunction] = Field(default_factory=list)
    function_call: LanguageModelFunction = None

    def get_messages(self):
        return [m.to_dict() for m in self.messages]

    def get_functions(self):
        return [f.to_dict() for f in self.functions]

    def get_function_call(self):
        if self.function_call is None:
            return None
        return self.function_call.json_schema or "auto"

    def __str__(self):
        return "\n\n".join([f"{m.role.value}: {m.content}" for m in self.messages])
            # + "\n\nFunctions:" + "\n\n".join([f"{f.json_schema}" for f in self.functions])


class LanguageModelResponse(LanguageModelProviderModelResponse):
    """Standard response struct for a response from a language model."""


class TaskType(str, enum.Enum):
    RESEARCH: str = "research"
    WRITE: str = "write"
    EDIT: str = "edit"
    CODE: str = "code"
    DESIGN: str = "design"
    TEST: str = "test"
    PLAN: str = "plan"


class TaskStatus(str, enum.Enum):
    BACKLOG: str = "backlog"
    READY: str = "ready"
    IN_PROGRESS: str = "in_progress"
    DONE: str = "done"


class TaskContext(BaseModel):
    cycle_count: int = 0
    status: TaskStatus = TaskStatus.BACKLOG
    parent: "Task" = None
    prior_actions: List[AbilityAction] = Field(default_factory=list)
    memories: list = Field(default_factory=list)
    user_input: List[str] = Field(default_factory=list)
    supplementary_info: List[str] = Field(default_factory=list)
    enough_info: bool = False


class Task(BaseModel):
    objective: str
    type: str  # TaskType  FIXME: gpt does not obey the enum parameter in its schema
    priority: int
    ready_criteria: List[str]
    acceptance_criteria: List[str]
    context: TaskContext = Field(default_factory=TaskContext)

    @classmethod
    def factory(
        cls,
        objective: str,
        type: str = TaskType.RESEARCH,
        priority: int = 1,
        ready_criteria: List[str] = None,
        acceptance_criteria: List[str] = None,
        context: TaskContext = None,
        **kwargs,
    ):
        if ready_criteria is None:
            ready_criteria = [""]
        if acceptance_criteria is None:
            acceptance_criteria = [""]
        if context is None:
            context = TaskContext()

        return cls(
            objective=objective,
            type=type,
            priority=priority,
            ready_criteria=ready_criteria,
            acceptance_criteria=acceptance_criteria,
            context=context,
        )

    def generate_kwargs(self) -> dict[str, str]:
        action_history = "\n".join(
            [str(action) for action in self.context.prior_actions]
        )
        additional_info = "\n".join(self.context.supplementary_info)
        user_input = "\n".join(self.context.user_input)
        acceptance_criteria = "\n".join(self.acceptance_criteria)

        return {
            "task_objective": self.objective,
            "cycle_count": self.context.cycle_count,
            "action_history": action_history,
            "additional_info": additional_info,
            "user_input": user_input,
            "acceptance_criteria": acceptance_criteria,
        }


# Need to resolve the circular dependency between Task and TaskContext once both models are defined.
TaskContext.update_forward_refs()


class ExecutionNature(str, enum.Enum):
    SIMPLE = "simple"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    AUTO = "auto"


class StepType(str, enum.Enum):
    SCHEDULAR = "schedular"
    PLANNER = "planner"
    EXECUTOR = "executor"
    COMMUNICATOR = "communicator"
