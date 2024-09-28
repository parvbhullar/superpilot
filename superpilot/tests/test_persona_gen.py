import asyncio
import os
import sys
import argparse
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from superpilot.examples.persona.executor import PersonaGenExecutor


def main(args):
    # Load the appropriate template
    persona_executor = PersonaGenExecutor()
    asyncio.run(persona_executor.execute(args))
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthesize text using a specified model and template.")
    parser.add_argument('--sample_size', type=int, default=2, help='Number of samples to process from the dataset; Set it to 0 if you want to use the full set of 200k personas.')
    parser.add_argument(
        '--template',
        type=str,
        default='instruction',
        choices=['instruction', 'knowledge', 'npc', 'math'],
        help=(
            "Prompt templates. Choose from 'instruction', 'knowledge', 'math' or 'npc'. "
            "You can also add more customized templates in prompt_templates.py"
        )
    )
    parser.add_argument(
        '--output_path',
        type=str,
        default='persona_output.jsonl',
        help='Path to the output file.')

    args = parser.parse_args()
    main(args)
#
# if __name__ == "__main__":
#     personas = [{
#         "input_persona": {
#             "type": "string",
#             "text": "A science journalist interested in interviewing the materials scientist to share their groundbreaking work with the public"
#         },
#         "synthesized_text": {
#             "type": "string",
#             "text": "The science journalist wants to interview a materials scientist about their groundbreaking work. The scientist is available for an interview only on the weekdays between 10 am and 4 pm. The journalist also has other commitments, including a daily news briefing from 11 am to 12 pm, a weekly editorial meeting every Tuesday from 2 pm to 3 pm, and an online course on advanced science communication every Thursday from 1 pm to 2 pm. Considering these schedules, what would be the optimal days and times for the journalist to interview the scientist without any conflicts?"
#         },
#         "description": {
#             "type": "string",
#             "class": "logical reasoning"
#         }
#     }]
#     persona_executor = PersonaGenExecutor()
#     asyncio.run(persona_executor.execute(personas))