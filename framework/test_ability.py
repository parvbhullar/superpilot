import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import json
import logging
from superpilot.framework.abilities import SearchAndSummarizeAbility, TextSummarizeAbility

import asyncio


# Assuming the class SearchAndSummarizeAbility is already defined in your code

# Define a logger
logger = logging.getLogger("SearchAndSummarizeAbility")


ability_arguments = {
    "query": "Write a blog on Future of Financial Services and LLMs",
    "context": ["AI", "Deep Learning"],
    "system_text": "SEARCH_AND_SUMMARIZE_SYSTEM"
}



# Pilot name and goals define

# Task Plan it will define task and execute it, if required generate more sub tasks and execute them as well - TaskPlanner

# Task Planner - List[Tasks] -> TaskExecutor
# 1. Ask to user to define the task
# 2. Reply with the task plan and ask for confirmation

# If flow is fixed in terms of abilities den task planner strategy should be according to the given flow.
# Mapping of steps and tasks should be defined in the task planner

# Flow could be defined as a sequence of tasks and abilities

# Flow execution strategy can be defined with prompt or sequential strategy, we will step, a step could be single, parralel or sequential

# Flow executor -
# Data gathar [WebSearch, KnowledgeBase, News] - parrallel] -> Analysis[FinancialAnalysis] -> Write[TextStream, PDF, Word] -> Respond[Twitter, Email, Stream]]


# Create ability instance
search_ability = SearchAndSummarizeAbility(
    logger=logger,
    configuration=SearchAndSummarizeAbility.default_configuration
)
ability = TextSummarizeAbility(
    logger=logger,
    configuration=SearchAndSummarizeAbility.default_configuration
)

content = ""

with open("superpilot/framework/content.txt", "r") as f:
    content = f.read()

# Extract the arguments
query = ability_arguments["query"]
context = ability_arguments["context"]
system_text = ability_arguments.get("system_text", "SEARCH_AND_SUMMARIZE_SYSTEM")

# Execute the ability (asynchronous call)
# result = asyncio.run(search_ability(query, context, system_text))
result = asyncio.run(ability([content], query))

# Print the result
print(result.content)
