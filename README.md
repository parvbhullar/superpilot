# Superpilot
LLM based multi-model framework for AI apps. The SuperPilot Framework is a robust architecture designed to 
build and execute various LLM app using prompt, abilities like text summarization, web searching, and more. 
It leverages machine learning models from providers like OpenAI to perform these tasks. The framework consists of 
several key components including OpenAI Provider, SimplePrompt, AbilityRegistry, and SuperTaskPilot, which are essential for smooth operation.

# SuperPilot Framework - Quickstart Guide

## Table of Contents
1. [Initializing OpenAI Provider](#initializing-openai-provider)
2. [Creating SimplePrompt](#creating-superprompt)
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

## Creating SimplePrompt

**Purpose:** To generate the prompt that will be passed to the OpenAI model for completion.

### Steps:
1. Import the SimplePrompt class.
2. Initialize a SimplePrompt object.
3. Build the prompt using `build_prompt()` method.

```python
from superpilot.core.planning.strategies.simple import SimplePrompt

super_prompt = SimplePrompt.factory()
prompt = super_prompt.build_prompt("Your Query Here")
```

# Using SimpleTaskPilot

## Initial Setup

Before running any queries, make sure all necessary modules are imported and environment variables, including the OpenAI API key, are set up.

## Making a Query

To make a query, utilize the `test_pilot()` function. The `query` string parameter specifies the information you're seeking.

### Example 1: Weather in Mumbai

```python
query = "What is the weather in Mumbai"
```

This query instructs SimpleTaskPilot to fetch weather information for Mumbai.

### Example 2: Stock Market Analysis

```python
query = "Analyze the stock market for today"
```

This query prompts SimpleTaskPilot to provide an analysis of today's stock market.

### Example 3: Email Summarization

```python
query = "Summarize the last 10 emails"
```

This query will lead SimpleTaskPilot to summarize the last 10 emails in your inbox.

### Example 4: News Highlights

```python
query = "Summarize today's top 5 news"
```

This query tasks SimpleTaskPilot with fetching and summarizing the day's top 5 news articles.

## Running the Query

After setting your query string, execute it with the following code:

```python
from superpilot.core.context.schema import Context
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIProvider,
    OpenAIModelName
)

context = Context()
# Load Model Providers
open_ai_provider = OpenAIProvider.factory(your_openai_api_key)
model_providers = {ModelProviderName.OPENAI: open_ai_provider}

task_pilot = SimpleTaskPilot(model_providers=model_providers)

print("***************** Executing SimplePilot ******************************\n")
query = "Summarize today's top 5 news"
response = await task_pilot.execute(query, context)
print(response)
print("***************** Executing SimplePilot Completed ******************************\n")

```

The output should be displayed on the console.

## Executing SuperTaskPilot

**Purpose:** To execute tasks using the registered abilities and model providers.

### Steps:
1. Import the `SuperTaskPilot` class.
2. Initialize it with the `super_ability_registry` and `model_providers`.


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

```python
from superpilot.core.pilot.task.super import SuperTaskPilot

search_step = SuperTaskPilot(super_ability_registry, model_providers)
```



**Credits:** This framework relies on [AutoGPT's](https://github.com/Significant-Gravitas/Auto-GPT/tree/master/autogpt/core) core library for its underlying functionalities.
