import json
import openai
import requests

# Initialize OpenAI API with your key
openai.api_key = ''



# VAPI Agent credentials
AGENT_ID = ''
API_KEY = ''
TWILIO_SID = ''
TWILIO_AUTH_TOKEN = ''
TWILIO_PHONE_NUMBER = ''

# VAPI API endpoint
VAPI_URL = 'https://vapi.ai?demo=true&shareKey=8c3e405d-060c-4497-9ee5-67b5a62505ce&assistantId=de8fe3dc-17e1-40d0-80ea-194ef678018f'

# Initial message to the user via agent
initial_content = "app ek ai agent hai apko sales ka bhut acha experience hai or app property sale purchase krwate hai app ek behtar vikalp laye hai for agent ."
user_prompt = "user se poocho apki zaroorate"

# Function to interact with OpenAI API to generate assistant response
def get_openai_response(user_input):
    response = openai.Completion.create(
        model="gpt-3.5-turbo",  # or other models as required
        prompt=user_input,
        max_tokens=150
    )
    return response.choices[0].text.strip()

# Function to send message to VAPI and get response (using GET request)
def send_message_to_agent():
    try:
        # Send the message to the API
        response = requests.post(VAPI_URL, json=data, headers=headers, params=params)

        # Print the raw response content for debugging
        print("Raw Response Content:", response.text)

        # Check if the response content type is JSON
        try:
            response_json = response.json()  # Attempt to parse JSON
            print("Response JSON:", json.dumps(response_json, indent=4))
        except requests.exceptions.JSONDecodeError:
            print(f"Error: Response is not valid JSON. Response content: {response.text}")

        # Handle other status codes
        if response.status_code != 200:
            print(f"Error: API request failed with status code {response.status_code}")
            print("Error Message:", response.text)

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

# Call the function
send_message_to_agent()

# If the response is not valid, exit the script
if not agent_response:
    print("No valid response received from the agent.")
    exit()

# Get user input (simulated for the sake of this script)
user_input = input("Please ask the agent your question: ")

# Generate assistant response using OpenAI based on user input
assistant_response = get_openai_response(user_input)

# Simulate sending the user message to the agent
user_message = {
    "role": "user",
    "content": user_input
}

# Prepare the complete JSON output with both responses
conversation_json = {
    "conversation": [
        {
            "role": "agent",
            "content": agent_response.get('content', 'No response from agent')
        },
        user_message,
        {
            "role": "assistant",
            "content": assistant_response
        }
    ]
}

# Output the conversation in JSON format
print(json.dumps(conversation_json, indent=4))
