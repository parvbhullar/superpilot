# Superpilot
LLM based multi-model framework for AI apps. The SuperPilot Framework is a robust architecture designed to 
build and execute various LLM app using prompt, abilities like text summarization, web searching, and more. 
It leverages machine learning models from providers like OpenAI to perform these tasks. The framework consists of 
several key components including OpenAI Provider, SuperPrompt, AbilityRegistry, and SuperTaskPilot, which are essential for smooth operation.

# SuperPilot Framework - Quickstart Guide

## Table of Contents
1. [Initializing OpenAI Provider](#initializing-openai-provider)
2. [Creating SuperPrompt](#creating-superprompt)
3. [Setting Up AbilityRegistry](#setting-up-abilityregistry)
4. [Executing SuperTaskPilot](#executing-supertaskpilot)

## Initializing OpenAI Provider

**Purpose:** To set up OpenAI as a model provider for handling language completions.

### Steps:
1. Import the necessary modules.
2. Use the `OpenAIProvider.factory()` method to create an OpenAI Provider instance.
3. Store this instance in the `model_providers` dictionary for later use.

```python
from superpilot.core.resource.model_providers import OpenAIProvider, ModelProviderName
from superpilot.core.configuration import get_config

config = get_config()
open_ai_provider = OpenAIProvider.factory(config.openai_api_key)
model_providers = {ModelProviderName.OPENAI: open_ai_provider}
```

## Creating SuperPrompt

**Purpose:** To generate the prompt that will be passed to the OpenAI model for completion.

### Steps:
1. Import the SuperPrompt class.
2. Initialize a SuperPrompt object.
3. Build the prompt using `build_prompt()` method.

```python
from superpilot.core.planning.strategies.super import SuperPrompt

super_prompt = SuperPrompt.factory()
prompt = super_prompt.build_prompt("Your Query Here")
```

## Setting Up AbilityRegistry

**Purpose:** To manage and register the abilities that your application will use.

### Steps:
1. Import the `SuperAbilityRegistry` class.
2. Initialize it with the allowed abilities.

```python
from superpilot.core.ability.super import SuperAbilityRegistry
from superpilot.tests.test_env_simple import get_env

env = get_env({})
ALLOWED_ABILITY = {
    TextSummarizeAbility.name(): TextSummarizeAbility.default_configuration,
}

super_ability_registry = SuperAbilityRegistry.factory(env, ALLOWED_ABILITY)
```

## Executing SuperTaskPilot

**Purpose:** To execute tasks using the registered abilities and model providers.

### Steps:
1. Import the `SuperTaskPilot` class.
2. Initialize it with the `super_ability_registry` and `model_providers`.

```python
from superpilot.core.pilot.task.super import SuperTaskPilot

search_step = SuperTaskPilot(super_ability_registry, model_providers)
```


**Credits:** This framework relies on [AutoGPT's](https://github.com/Significant-Gravitas/Auto-GPT/tree/master/autogpt/core) core library for its underlying functionalities.
