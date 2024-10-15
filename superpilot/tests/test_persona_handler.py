import asyncio
import os
import sys
import argparse
import json
from typing import Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.examples.persona.schema import Message, User, Role, Context
from superpilot.examples.persona.handler import PersonaHandler


agent_json = {
                "persona_name": "HeritageReviver",
                "tags": [
                    "preservation architecture",
                    "adaptive reuse",
                    "historic buildings",
                    "community development",
                    "Midwestern towns"
                ],
                "handle": "heritage-reviver",
                "about": "An expert in preservation architecture focusing on revitalizing historic commercial buildings in Midwestern communities, ensuring the balance between historical integrity and modern utility.",
                "persona": "HeritageReviver is dedicated to the adaptive reuse of historic commercial buildings, emphasizing the importance of preserving the architectural heritage of Midwestern towns. By revitalizing Main Street USA, HeritageReviver explores how these efforts positively affect community identity and economic development. With a focus on sustainability and resilience, this persona highlights how careful preservation can foster a sense of place while addressing contemporary needs. Through thoughtful integration of old structures into modern uses, HeritageReviver aims to inspire communities to cherish their history while embracing future growth.",
                "knowledge_bases": [
                    "Preservation Architecture Resources",
                    "Midwestern Heritage Studies",
                    "Community Development Initiatives"
                ]
            }

async def call_agent(agent: dict, message: Message) -> Any:
    """
    Call a single agent asynchronously.
    """
    try:
        agent = agent.get("metadata", agent)
        if not agent.get("persona", None):
            print(f"Error finding agent {agent}.")
            return None
        pilot = PersonaHandler.from_json(agent)
        # pilot = DSPyHandler.from_json(agent)
        response = await pilot.execute(message, Context.factory("Session1"), None)
        # print(response)
        msg = Message.from_model_response(response, message.session_id,
                                          User.add_user(pilot.name(), Role.ASSISTANT, data=pilot.dump()))
        # self._context.add_message(msg)
        # if self.callback:
        #     self.callback.send(msg)
        return msg
    except Exception as e:
        print(f"Error calling agent {agent}: {str(e)}")
        return None

if __name__ == "__main__":
    message = Message.create("Top historical events in the world")
    response = asyncio.run(call_agent(agent_json, message))
    print(response)