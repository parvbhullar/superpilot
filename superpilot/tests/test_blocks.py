class FormBlock:
    def __init__(self, title, description, icon, form_type):
        self.title = title
        self.description = description
        self.icon = icon
        self.type = form_type
        self.input_fields = {
            'GSTIN': '',
            'FY': ''
        }
        self.output_fields = {}

    def collect_input(self):
        self.input_fields['GSTIN'] = input("Enter GSTIN: ")
        self.input_fields['FY'] = input("Enter FY: ")

    def get_output(self):
        self.output_fields = self.input_fields
        return self.output_fields


import requests

class ApiBlock:
    def __init__(self, title, description, icon, block_type, url, method, headers):
        self.title = title
        self.description = description
        self.icon = icon
        self.type = block_type
        self.url = url
        self.method = method
        self.headers = headers
        self.input_fields = {}
        self.output_fields = {}

    def set_input(self, gstin, fy):
        self.input_fields['GSTIN'] = gstin
        self.input_fields['FY'] = fy

    def call_api(self):
        payload = {
            'GSTIN': self.input_fields['GSTIN'],
            'FY': self.input_fields['FY']
        }
        response = requests.get(self.url, headers=self.headers, params=payload)
        if response.status_code == 200:
            self.output_fields = response.json()
        else:
            self.output_fields = {'error': 'API call failed'}
        return self.output_fields


import openai

class LLMBlock:
    def __init__(self, title, description, icon, block_type, model_name, model_temp, system_prompt):
        self.title = title
        self.description = description
        self.icon = icon
        self.type = block_type
        self.model_name = model_name
        self.model_temp = model_temp
        self.system_prompt = system_prompt
        self.input_fields = {}
        self.output_fields = {}

    def set_input(self, gstin, fy, api_response):
        self.input_fields['GSTIN'] = gstin
        self.input_fields['FY'] = fy
        self.input_fields['api_response'] = api_response

    def call_llm(self):
        openai.api_key = "your_openai_api_key"
        response = openai.Completion.create(
            engine=self.model_name,
            prompt=self.system_prompt + str(self.input_fields['api_response']),
            max_tokens=150,
            temperature=self.model_temp,
        )
        self.output_fields['response'] = response.choices[0].text.strip()
        return self.output_fields


import requests


class PushDataBlock:
    def __init__(self, title, description, icon, block_type, url, method, headers):
        self.title = title
        self.description = description
        self.icon = icon
        self.type = block_type
        self.url = url
        self.method = method
        self.headers = headers
        self.input_fields = {}
        self.output_fields = {}

    def set_input(self, summary, fy, gstin):
        self.input_fields['Summary'] = summary
        self.input_fields['FY'] = fy
        self.input_fields['GSTIN'] = gstin

    def call_api(self):
        payload = {
            'Summary': self.input_fields['Summary'],
            'FY': self.input_fields['FY'],
            'GSTIN': self.input_fields['GSTIN']
        }
        response = requests.post(self.url, headers=self.headers, json=payload)
        if response.status_code == 200:
            self.output_fields = response.json()
        else:
            self.output_fields = {'error': 'API call failed'}
        return self.output_fields


# Example usage
if __name__ == "__main__":
    # from form_block import FormBlock
    # from api_block import ApiBlock
    # from llm_block import LLMBlock
    # from base import PushDataBlock

    # Step 1: Form Block
    form_block = FormBlock(title="Form Block -> GST API Block", description="", icon="", form_type="Form")
    form_block.collect_input()
    form_output = form_block.get_output()

    # Step 2: API Block
    api_block = ApiBlock(title="Gstin API", description="", icon="", block_type="API",
                         url="http://mi.com./gstin/verification", method="GET",
                         headers={"api-key": "Key-skjfaksh-abfc", "product_id": "pId"})
    api_block.set_input(gstin=form_output['GSTIN'], fy=form_output['FY'])
    api_output = api_block.call_api()

    # Step 3: LLM/Agent Block
    llm_block = LLMBlock(title="Agent",
                         description="Will create summary from the LLM from given json data from previous block.",
                         icon="", block_type="LLM", model_name="gpt-3.5-turbo", model_temp=0.5,
                         system_prompt="You are a smart AI agent which will create summary of a particular business GSTIN status from given response in JSON.")
    llm_block.set_input(gstin=form_output['GSTIN'], fy=form_output['FY'], api_response=api_output)
    llm_output = llm_block.call_llm()

    # Step 4: Push Data to External API Block
    push_data_block = PushDataBlock(title="Push data to external API", description="", icon="", block_type="API",
                                    url="http://mi.com./push/verification/data", method="POST",
                                    headers={"api-key": "Key-skjfaksh-abfc", "product_id": "pId"})
    push_data_block.set_input(summary=llm_output['response'], fy=form_output['FY'], gstin=form_output['GSTIN'])
    push_data_output = push_data_block.call_api()

    print(push_data_output)


if __name__ == "__main__":
    push_data_block = PushDataBlock(title="Push data to external API",
                                    description="",
                                    icon="",
                                    block_type="API",
                                    url="http://mi.com./push/verification/data",
                                    method="POST",
                                    headers={"api-key": "Key-skjfaksh-abfc", "product_id": "pId"})
    push_data_block.set_input(summary="Sample summary", fy="2021-2022", gstin="sampleGSTIN")
    print(push_data_block.call_api())


# Example usage
if __name__ == "__main__":
    llm_block = LLMBlock(title="Agent",
                         description="Will create summary from the LLM from given json data from previous block.",
                         icon="",
                         block_type="LLM",
                         model_name="gpt-3.5-turbo",
                         model_temp=0.5,
                         system_prompt="You are a smart AI agent which will create summary of a particular business GSTIN status from given response in JSON.")
    llm_block.set_input(gstin="sampleGSTIN", fy="2021-2022", api_response={"name": "Sample", "status": "Active"})
    print(llm_block.call_llm())

# Example usage
if __name__ == "__main__":
    api_block = ApiBlock(title="Gstin API",
                         description="",
                         icon="",
                         block_type="API",
                         url="http://mi.com./gstin/verification",
                         method="GET",
                         headers={"api-key": "Key-skjfaksh-abfc", "product_id": "pId"})
    api_block.set_input(gstin="sampleGSTIN", fy="2021-2022")
    print(api_block.call_api())


# Example usage
if __name__ == "__main__":
    form_block = FormBlock(title="Form Block -> GST API Block",
                           description="",
                           icon="",
                           form_type="Form")
    form_block.collect_input()
    print(form_block.get_output())
