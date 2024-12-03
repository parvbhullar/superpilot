

import os
import sys
import asyncio
import time
from dotenv import load_dotenv

load_dotenv(verbose=True, override=True)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.examples.email.agents_search import AgentSearchSystem

agent = AgentSearchSystem(api_url='http://qa-search-service.co/api/v1/search/query/agents/')

print(agent.run(query='Most important inventions of the 21st century'))
