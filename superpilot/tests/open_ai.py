import base64
import requests
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.examples.ed_tech.question_executor import QuestionExecutor
# OpenAI API Key
api_key = os.environ.get("OPENAI_API_KEY")
# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Path to your image
image_path = "/Users/parvbhullar/Drives/Vault/Projects/Unpod/superpilot/superpilot/docs/ImagebasedQs/Q2.png"
image_path = "/Users/parvbhullar/Drives/Vault/Projects/Unpod/superpilot/superpilot/docs/ImagebasedQs/Q2.png"
image_path = "/Users/parvbhullar/Drives/Vault/Projects/Unpod/superpilot/superpilot/docs/ImagebasedQs/Q1.jpeg"

# Getting the base64 string
base64_image = encode_image(image_path)

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

payload = {
    "model": "gpt-4-vision-preview",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "Extract the question with latex given in the image also explaining given figures or diagrams but do not answer the question."
                    "Q:"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": f"data:image/jpeg;base64,{base64_image}"
            }
          }
        ]
      }
    ],
    "max_tokens": 300
}

response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

print(response.json())