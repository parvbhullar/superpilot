import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
import logging
from superpilot.framework.abilities import SearchAndSummarizeAbility, TextSummarizeAbility

from typing import List, Dict
from typing_extensions import Literal
import asyncio
from superpilot.core.flow.simple import SimpleTaskPilot

class Step:
    def __init__(self, task: Task, abilities: List[Ability], execution_nature: Literal['single', 'parallel', 'seq']):
        self.task = task
        self.abilities = abilities
        self.execution_nature = execution_nature

    async def execute(self, **kwargs):
        if self.execution_nature == 'parallel':
            tasks = [ability(**kwargs) for ability in self.abilities]
            await asyncio.gather(*tasks)
        else:
            for ability in self.abilities:
                await ability(**kwargs)


class TaskPlanner:
    def __init__(self, flow: 'Flow'):
        self.flow = flow
        self.tasks = []

    def define_task(self, task: Task):
        self.tasks.append(task)

    async def execute(self, **kwargs):
        print("Task plan:")
        for task in self.tasks:
            print(f" - {task.name}")

        confirmation = input("Confirm execution? (y/n): ")
        if confirmation.lower() == 'y':
            for task in self.tasks:
                await task.execute(**kwargs)


class Flow:
    def __init__(self, steps: List[Step], strategy: Literal['prompt', 'seq'] = 'seq'):
        self.steps = steps
        self.strategy = strategy

    async def execute(self, **kwargs):
        if self.strategy == 'prompt':
            await self._execute_with_prompt(**kwargs)
        else:
            await self._execute_sequential(**kwargs)

    async def _execute_with_prompt(self, **kwargs):
        for step in self.steps:
            print(f"Executing step: {step.name}")
            await step.execute(**kwargs)
            input("Press Enter to continue...")

    async def _execute_sequential(self, **kwargs):
        for step in self.steps:
            await step.execute(**kwargs)


# Flow executor -
# Data gathar [WebSearch, KnowledgeBase, News] - parrallel] -> Analysis[FinancialAnalysis] -> Write[TextStream, PDF, Word] -> Respond[Twitter, Email, Stream]]
