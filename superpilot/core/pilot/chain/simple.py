from .base import BaseChain


class SimpleChain(BaseChain):
    async def execute_handler(self, pilot, task, context, **kwargs):
        return await pilot.execute(task, context, **kwargs)