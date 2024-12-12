# Superpilot
LLM based multi-model framework for AI applications. The SuperPilot Framework provides a robust architecture for
building and executing various LLM-powered applications using a system of pilots, abilities, and task management.
It leverages machine learning models from providers like OpenAI to perform complex tasks autonomously. The framework consists of
several key components including SuperPilot, SuperTaskPilot, and SuperAbilityRegistry, which work together to enable
autonomous task planning and execution.

# SuperPilot Framework - Quickstart Guide

## Table of Contents
1. [Core Components Overview](#core-components-overview)
2. [Getting Started](#getting-started)
3. [SuperPilot Usage](#superpilot-usage)
4. [SuperTaskPilot Usage](#supertaskpilot-usage)
5. [Working with Abilities](#working-with-abilities)

## Core Components Overview

### SuperPilot
The main pilot class for autonomous task execution. It handles:
- Autonomous task planning and execution
- Integration with ability registry
- Memory management
- Task queue management
- Model provider integration

### SuperTaskPilot
Task-specific pilot implementation for executing individual tasks:
- Supports sequential/parallel execution modes
- Integrates with language models
- Manages ability execution
- Configurable execution strategies

### SuperAbilityRegistry
Registry for managing and executing abilities:
- Dynamic ability registration
- Environment integration
- Model provider management
- Built-in ability support

## Getting Started

### Prerequisites
- Python 3.7+
- OpenAI API key
- Required packages installed

### Installation
```bash
# Clone the repository
git clone https://github.com/parvbhullar/superpilot.git
cd superpilot

# Install dependencies
pip install -r requirements.txt

# Install the package
python setup.py install
```

### Basic Setup
```python
from superpilot.core.pilot import SuperPilot
from superpilot.core.ability.super import SuperAbilityRegistry
from superpilot.core.resource.model_providers import OpenAIProvider, ModelProviderName
from superpilot.tests.test_env_simple import get_env

# Initialize environment
env = get_env({})
planner = env.get("planning")
ability_registry = env.get("ability_registry")

# Create and initialize SuperPilot
pilot = SuperPilot(SuperPilot.default_settings, ability_registry, planner, env)
await pilot.initialize("Your objective here")
```

## SuperPilot Usage
```python
from typing import Dict, List
from superpilot.core.pilot import SuperPilot
from superpilot.core.ability.super import SuperAbilityRegistry
from superpilot.core.resource.model_providers import OpenAIProvider, ModelProviderName
from superpilot.core.context.schema import Context
from superpilot.tests.test_env_simple import get_env

async def run_superpilot(objective: str) -> Context:
    """
    Execute a task using SuperPilot with automatic task planning and execution.

    Args:
        objective: The high-level objective to accomplish

    Returns:
        Context object containing the execution results
    """
    # Initialize environment and components
    env = get_env({})
    planner = env.get("planning")
    ability_registry = env.get("ability_registry")

    # Create and initialize SuperPilot
    pilot = SuperPilot(SuperPilot.default_settings, ability_registry, planner, env)
    await pilot.initialize(objective)

    # Execute the task and get results
    context = await pilot.execute(objective)
    return context

# Example usage
objective = "Summarize today's top 5 news articles"
context = await run_superpilot(objective)
print(context.format_numbered())
```

## SuperTaskPilot Usage
```python
from typing import Dict, List
from superpilot.core.pilot.task.super import SuperTaskPilot
from superpilot.core.ability.super import SuperAbilityRegistry
from superpilot.core.resource.model_providers import OpenAIProvider, ModelProviderName
from superpilot.core.context.schema import Context
from superpilot.core.planning.schema import Task
from superpilot.tests.test_env_simple import get_env

async def execute_parallel_tasks(tasks: List[str]) -> List[Context]:
    """
    Execute multiple tasks in parallel using SuperTaskPilot.

    Args:
        tasks: List of task objectives to execute in parallel

    Returns:
        List of Context objects containing results for each task
    """
    # Initialize environment
    env = get_env({})
    ability_registry = env.get("ability_registry")
    model_providers = {ModelProviderName.OPENAI: OpenAIProvider.factory()}

    # Create task pilot
    task_pilot = SuperTaskPilot(ability_registry, model_providers)

    # Create Task objects
    task_objects = [
        Task(
            objective=task,
            priority=1,
            type="text",
            ready_criteria=[],
            acceptance_criteria=[]
        ) for task in tasks
    ]

    # Execute tasks in parallel
    results = await asyncio.gather(*[
        task_pilot.execute(task) for task in task_objects
    ])
    return results

# Example usage
tasks = [
    "Analyze market trends",
    "Summarize competitor news",
    "Generate performance report"
]
results = await execute_parallel_tasks(tasks)
for task, result in zip(tasks, results):
    print(f"\nResults for {task}:")
    print(result.format_numbered())
```

## Working with Abilities
```python
from typing import Dict, Any
from superpilot.core.ability.super import SuperAbilityRegistry
from superpilot.framework.abilities import TextSummarizeAbility
from superpilot.tests.test_env_simple import get_env

async def register_and_use_abilities(
    abilities_config: Dict[str, Any]
) -> SuperAbilityRegistry:
    """
    Register and configure abilities for use with SuperPilot.

    Args:
        abilities_config: Dictionary mapping ability names to their configurations

    Returns:
        Configured SuperAbilityRegistry instance
    """
    # Initialize environment
    env = get_env({})

    # Create ability registry with custom configuration
    ability_registry = SuperAbilityRegistry.factory(env, abilities_config)

    return ability_registry

# Example usage
abilities_config = {
    TextSummarizeAbility.name(): TextSummarizeAbility.default_configuration,
    # Add more abilities with their configurations
}

registry = await register_and_use_abilities(abilities_config)
ability = registry.get_ability("TextSummarizeAbility")
result = await ability.execute(
    query="Summarize the quarterly report",
    max_tokens=500
)
print(result.content)
```

**Credits:** This framework builds upon concepts from [AutoGPT's](https://github.com/Significant-Gravitas/Auto-GPT/tree/master/autogpt/core) core library while implementing its own unique architecture for autonomous task execution.
