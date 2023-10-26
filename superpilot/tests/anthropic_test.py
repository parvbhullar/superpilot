import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
# from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
#
# anth = Anthropic(
#     # defaults to os.environ.get("ANTHROPIC_API_KEY")
# )
#
# completion = anth.completions.create(
#     model="claude-2",
#     max_tokens_to_sample=300,
#     prompt=f"{HUMAN_PROMPT} how does a court case get to the Supreme Court?{AI_PROMPT}",
# )
#
# print(completion.completion)