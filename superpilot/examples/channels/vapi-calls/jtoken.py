import requests

auth_token = ''
phone_number_id = ''
customer_number = ""

# Create the header with Authorization token
headers = {
    'Authorization': f'Bearer {auth_token}',
    'Content-Type': 'application/json',
}

data = {
    'assistant': {
        "id": "",  
        "firstMessage": "Hey, what's up?",
        "voice": "jennifer-playht"
    },
    'phoneNumberId': phone_number_id,
    'customer': {
        'number': customer_number,
    },
}

response = requests.post(
    'https://api.vapi.ai/call/phone', headers=headers, json=data)

if response.status_code == 201:
    print('Call created successfully')
    print(response.json())
else:
    print('Failed to create call')
    print(response.text)
