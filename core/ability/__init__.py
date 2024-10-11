"""The command system provides a way to extend the functionality of the AI pilot."""
from superpilot.core.ability.base import Ability, AbilityRegistry
from superpilot.core.ability.simple import AbilityRegistrySettings, SimpleAbilityRegistry
from superpilot.core.ability.super import SuperAbilityRegistry
from superpilot.core.ability.schema import AbilityAction
from superpilot.core.status import ShortStatus, Status

status = Status(
    module_name=__name__,
    short_status=ShortStatus.IN_PROGRESS,
    handoff_notes=(
        "Before times: More work is needed, basic ideas are in place.\n"
        "5/16: Provided a rough interface, but we won't resolve this system til we need to use it.\n"
    ),
)
