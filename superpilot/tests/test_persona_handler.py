import asyncio
import os
import sys
import argparse
import json
from typing import Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.examples.persona.schema import Message, User, Role, Context
from superpilot.examples.persona.handler import PersonaHandler
from superpilot.examples.persona.query_process import query_process_agent


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
    ground_truth="""
    World War II (1939-1945) was the most devastating and widespread conflict in human history, involving more than 100 million people from over 30 countries. It began with Germany's invasion of Poland on September 1, 1939, prompting Britain and France to declare war on Germany. The war was primarily fought between the Axis Powers—Germany, Italy, and Japan—and the Allies, including Britain, France, the Soviet Union, China, and the United States.

    **Historical Context:** The roots of World War II can be traced back to the aftermath of World War I and the Treaty of Versailles (1919), which imposed harsh penalties on Germany. Economic instability, nationalism, and resentment fueled the rise of Adolf Hitler and the Nazi Party in Germany, which sought to restore German power and expand its territory. In the Pacific, Japan pursued imperial expansion, invading China in 1937. Italy, under Benito Mussolini, also sought to build a new Roman Empire, leading to invasions in Africa and Europe.

    **Geopolitical Impact:** The war dramatically reshaped global geopolitics. The defeat of Nazi Germany, Imperial Japan, and Fascist Italy ended the Axis threat, but it also gave rise to the Cold War. The United States and the Soviet Union emerged as the two dominant superpowers, with conflicting ideologies—capitalism and communism—driving decades of tension. Europe's influence declined as many of its colonies in Africa, Asia, and the Middle East sought independence, leading to the decolonization movement. Germany was divided into East and West, and Japan was occupied by U.S. forces until 1952.

    **Economic Effects:** The economic toll of World War II was staggering. Europe and Asia were left in ruins, with industries destroyed and millions displaced. The U.S. economy, however, emerged stronger, having ramped up production for the war effort and avoided destruction on its soil. The Marshall Plan, launched by the U.S. in 1948, helped rebuild Europe and restore economic stability. In contrast, the Soviet Union expanded its control over Eastern Europe, imposing communist regimes, which led to the creation of the Eastern Bloc.

    **World Trade and Globalization:** The war disrupted global trade, but it also laid the groundwork for modern international trade systems. Institutions like the United Nations, World Bank, and International Monetary Fund were created to promote peace, economic cooperation, and stability. The war also spurred technological advancements, such as radar, jet engines, and nuclear energy, which would shape global industries in the post-war era.

    Overall, World War II reshaped political alliances, economies, and international relations, setting the stage for the modern world.
    """
    query="Most important Historical Event of 21st Century"
    response = asyncio.run(query_process_agent(query=query,ground_truth=ground_truth))
    print(response)