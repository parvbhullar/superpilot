"""The Agent is an autonomouos entity guided by a LLM provider."""
from superpilot.core.pilot.base import Agent
from superpilot.core.pilot.settings import AgentSettings
from superpilot.core.pilot.simple import SimpleAgent
from superpilot.core.pilot.research import ResearchAgent
from superpilot.core.status import ShortStatus, Status

status = Status(
    module_name=__name__,
    short_status=ShortStatus.INTERFACE_DONE,
    handoff_notes=(
        "Before times: Sketched out Agent.__init__\n"
        "5/7: Interface has been created. Work is needed on the pilot factory.\n"
        "5/8: Agent factory has been adjusted to use the new plugin system."
        "5/15: Get configuration compilation working.\n"
        "5/16: Agent can boot strap and stand up. Working on taking an execution step.\n"
    ),
)
