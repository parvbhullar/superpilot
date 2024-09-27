import asyncio
import json
import os
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from superpilot.examples.persona.executor import PersonaGenExecutor


if __name__ == "__main__":
    personas = [{
        "input_persona": {
            "type": "string",
            "text": "A science journalist interested in interviewing the materials scientist to share their groundbreaking work with the public"
        },
        "synthesized_text": {
            "type": "string",
            "text": "The science journalist wants to interview a materials scientist about their groundbreaking work. The scientist is available for an interview only on the weekdays between 10 am and 4 pm. The journalist also has other commitments, including a daily news briefing from 11 am to 12 pm, a weekly editorial meeting every Tuesday from 2 pm to 3 pm, and an online course on advanced science communication every Thursday from 1 pm to 2 pm. Considering these schedules, what would be the optimal days and times for the journalist to interview the scientist without any conflicts?"
        },
        "description": {
            "type": "string",
            "class": "logical reasoning"
        }
    }]
    persona_executor = PersonaGenExecutor()
    asyncio.run(persona_executor.execute(personas))