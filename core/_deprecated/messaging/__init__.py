"""The messaging system provides a protocol for Agent communication with other pilots and users."""
from superpilot.core.status import ShortStatus, Status

status = Status(
    module_name=__name__,
    short_status=ShortStatus.BASIC_DONE,
    handoff_notes=(
        "Before times: Interface has been completed and a basic implementation has been created."
    ),
)
