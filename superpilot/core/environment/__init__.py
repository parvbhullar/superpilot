"""The Environment is an env entity which can be used by a pilot, step, or ability."""
from superpilot.core.status import ShortStatus, Status
from superpilot.core.environment.base import Environment
from superpilot.core.environment.settings import EnvSettings
from superpilot.core.environment.simple import SimpleEnv
from superpilot.core.status import ShortStatus, Status

status = Status(
    module_name=__name__,
    short_status=ShortStatus.INTERFACE_DONE,
    handoff_notes=(
        "Before times: Sketched out Env.__init__\n"
        "5/7: Interface has been created. Work is needed on the environment factory.\n"
        "5/8: Env factory has been adjusted to use the new plugin system."
        "5/15: Get configuration compilation working.\n"
        "5/16: Env can boot strap and stand up. Working on taking an execution step.\n"
    ),
)
