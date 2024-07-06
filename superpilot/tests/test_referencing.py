import json


def get_value_from_nested_dict(data, keys):
    for key in keys:
        data = data[key]
    return data


def set_value_in_nested_dict(data, keys, value):
    for key in keys[:-1]:
        data = data.setdefault(key, {})
    data[keys[-1]] = value


def load_values_from_previous_block(blocks):
    previous_block = blocks[0]
    next_block = blocks[1]

    previous_input_schema = json.loads(previous_block['input_schema'])
    next_input_schema = json.loads(next_block['input_schema'])

    for key, value in next_input_schema['query_params'].items():
        if 'reference' in value:
            reference_path = value['reference'].split('.')
            value_from_previous = get_value_from_nested_dict(previous_input_schema, reference_path[1:])
            set_value_in_nested_dict(next_input_schema, ['query_params', key, 'value'], value_from_previous)

    next_block['input_schema'] = json.dumps(next_input_schema)


# Sample blocks data
blocks = [
    {
        "id": 0,
        "location": "some_location",
        "block_type": "form",
        "metadata": """{
            "name": "form Block",
            "description": "Form To get values",
            "config": {}
        }""",
        "input_schema": """{
            "gstin": {
                "type": "string",
                "description": "The GSTIN to search for.",
                "value": "sadfasd fsfasdsfsa"
            },
            "query_params": {
                "fy": {
                    "type": "string",
                    "description": "The FY to search for.",
                    "value": "2023-24"
                }
            }
        }""",
        "output_schema": """{}""",
        "body": "",
        "seq_order": 0
    },
    {
        "id": 1,
        "location": "another_location",
        "block_type": "api",
        "metadata": """{
            "name": "API Block",
            "description": "A block that interacts with the API.",
            "config": {
                "url": "https://commonapi.mastersindia.co/commonapis/searchgstin",
                "method": "GET",
                "headers": {
                    "Authorization": "Bearer 9064e672f30ed03e2ac8e24d86279e7f36c2bd82",
                    "client_id": "JarZChUcsytSBbnkpt"
                }
            }
        }""",
        "input_schema": """{
            "query_params": {
                "gstin": {
                    "type": "string",
                    "description": "The GSTIN to search for.",
                    "reference": "block_0.gstin",
                    "value": ""
                },
                "fy": {
                    "type": "string",
                    "description": "The FY to search for.",
                    "reference": "block_0.query_params.fy",
                    "value": ""
                }
            },
            "headers": {},
            "payload": {}
        }""",
        "output_schema": """{
            "response": {
                "type": "object",
                "description": "The response from the API."
            }
        }""",
        "body": "",
        "seq_order": 1
    }
]

# Load values from the previous block into the next block
load_values_from_previous_block(blocks)

# Print the updated blocks to verify the values are loaded correctly
print(json.dumps(blocks, indent=4))
