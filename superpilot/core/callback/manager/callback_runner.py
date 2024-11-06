import asyncio
from typing import List, Any

from superpilot.core.callback.handler.base import BaseCallbackHandler


async def handle_event(
        handlers: List[BaseCallbackHandler],
        event_name: str,
        *args: Any,
        **kwargs: Any,
) -> None:
    try:
        coros = []
        for handler in handlers:
            event = getattr(handler, event_name)
            coros.append(event(*args, **kwargs))
        await asyncio.gather(*coros)
    except Exception as e:
        print("Exception in handle_event", e)
