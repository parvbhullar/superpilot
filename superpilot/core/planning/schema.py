import enum
from typing import List

from pydantic import BaseModel, Field

from superpilot.core.ability.schema import AbilityAction
from superpilot.core.resource.model_providers.schema import (
    LanguageModelFunction,
    LanguageModelMessage,
    LanguageModelProviderModelResponse, SchemaModel,
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
    default_memory: list = Field(default_factory=list)
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
        if kwargs and "status" in kwargs:
            context.status = kwargs["status"]

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

    def update_memory(self, memory: list):
        self.check_context()
        self.context.memories += memory

    def set_default_memory(self, memory: list):
        self.check_context()
        self.context.default_memory = memory
        self.context.memories = memory

    def check_context(self):
        if self.context is None:
            self.context = TaskContext()
        return True


# Need to resolve the circular dependency between Task and TaskContext once both models are defined.
TaskContext.update_forward_refs()


class TaskSchema(SchemaModel):
    """
    Class representing the data structure for task for pilot objective, whether it is complete or not.
    """
    objective: str = Field(..., description="An verbose description of the task.")
    type: TaskType = Field(
        default=TaskType.RESEARCH,
        description="A categorization for the task from [research, write, edit, code, design, test, plan].")
    priority: int = Field(..., description="A number between 1 and 10 indicating the priority of the task "
                                           "relative to other generated tasks.")
    ready_criteria: List[str] = Field(..., description="A list of measurable and testable criteria that must "
                                                       "be met for the "
                                                       "task to be considered complete.")
    acceptance_criteria: List[str] = Field(..., description="A list of measurable and testable criteria that "
                                                            "must be met before the task can be started.")
    status: TaskStatus = Field(
        default=TaskStatus.BACKLOG,
        description="The current status of the task from [backlog, in_progress, complete, on_hold].")
    function_name: str = Field(..., description="Name of the pilot/function most suited for this task")
    motivation: str = Field(..., description="Your justification for choosing this pilot instead of a different one.")
    self_criticism: str = Field(..., description="Thoughtful self-criticism that explains why this pilot may not be "
                                                 "the best choice.")
    reasoning: str = Field(..., description="Your reasoning for choosing this pilot taking into account the "
                                            "`motivation` and weighing the `self_criticism`.")

    def get_task(self) -> Task:
        return Task.factory(self.objective, self.type, self.priority, self.ready_criteria, self.acceptance_criteria, status=self.status)


class ObjectivePlan(SchemaModel):
    """
    Class representing the data structure for observation for pilot objective, whether it is complete or not.
    If not complete, then the pilot name, motivation, self_criticism and reasoning for choosing the pilot.
    """
    current_status: TaskStatus = Field(..., description="Status of the objective asked by the user ")

    tasks: List[TaskSchema] = Field(
        ..., description="List of tasks to be accomplished by the each pilot"
    )

    def get_tasks(self) -> List[Task]:
        lst = []
        for task in self.tasks:
            lst.append(task.get_task())
        return lst
