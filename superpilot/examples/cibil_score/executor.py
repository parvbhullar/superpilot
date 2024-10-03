import asyncio
import io
import json
import os
import boto3
import random
import pdfplumber  
import requests
import openai
import pandas as pd
from superpilot.examples.executor.base import BaseExecutor
# client = OpenAI(
#     api_key=os.environ.get('OPENAI_API_KEY')
#     # other configurations...
# )
openai.api_key = os.environ.get('OPENAI_API_KEY')


class CibilScoreExecutor(BaseExecutor):

    def __init__(self, randomness=0.1, **kwargs):
        super().__init__(**kwargs)
        self.randomness = randomness

    def extract_pdf_content(self, pdf_binary_content):
        page_contents = []  # Array to hold content from each page
        try:
            with pdfplumber.open(io.BytesIO(pdf_binary_content)) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        page_contents.append(text)  # Append page text to the array
                        print(f"Extracted from page {i + 1}: {text[:100]}...")  # Print first 100 chars for inspection
            return page_contents  # Return the array of page contents
        except Exception as e:
            print(f"Error extracting PDF content: {e}")
            return []

    async def execute(self, files):
        if not files:
            print("No files provided")
            return None

        s3_url = files[0]['media_url']

        try:
            print("Downloading file from S3...")
            response = requests.get(s3_url)
            response.raise_for_status()
            file_content = response.content

            print("Extracting PDF content...")
            pdf_text_array = self.extract_pdf_content(file_content)

            if not pdf_text_array:
                print("No text extracted from PDF.")
                return None

            print("Extracted PDF text successfully.")  # Log successful extraction

            # Create a list to hold all loan information
            all_loans_info = []

            # Iterate over each page's text to extract loan information
            for page_text in pdf_text_array:
                # Enhanced query for each page
                query = f"""
                PDF CONTENT: {page_text}
                
                Please extract **all** loan information, including all credit card details, 
                and present it in JSON format. Include details like:
                - Loan Type
                - Borrower Name
                - Loan Amount
                - Interest Rate
                - Loan Term
                - Start Date
                - Payment Schedule
                - Status
                - Any other relevant information for each loan.

                Make sure to include every single loan entry in the output.
                """

                function_definitions = [
                    {
                        "name": "extract_loan_info",
                        "description": "Extracts loan and consumer credit information from the uploaded document",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "Consumer": {
                                    "type": "object",
                                    "properties": {
                                        "Name": {"type": "string"},
                                        "Date of Birth": {"type": "string"},
                                        "Gender": {"type": "string"},
                                        "PAN": {"type": "string"},
                                        "Driver's License": {"type": "string"},
                                        "UID": {"type": "string"},
                                        "CKYC": {"type": "string"},
                                        "Mobile Phones": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "Emails": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "Addresses": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "Type": {"type": "string"},
                                                    "Address": {"type": "string"},
                                                    "Reported Date": {"type": "string"},
                                                    "Residence Code": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                },
                                "Loans": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "Type": {"type": "string"},
                                            "Ownership": {"type": "string"},
                                            "Opened": {"type": "string"},
                                            "Last Payment": {"type": "string"},
                                            "Closed": {"type": "string"},
                                            "Sanctioned": {"type": "number"},
                                            "Current Balance": {"type": "number"},
                                            "Credit Limit": {"type": "number"},
                                            "Cash Limit": {"type": "number"},
                                            "Actual Payment": {"type": "number"},
                                            "EMI": {"type": "number"},
                                            "Payment History": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "Date": {"type": "string"},
                                                        "Days Past Due": {"type": "string"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "required": ["Consumer", "Loans"]
                        }
                    }
                ]

                response = openai.ChatCompletion.create(
                    messages=[
                        {
                            "role": "user",
                            "content": query,
                        }
                    ],
                    functions=function_definitions,
                    function_call="auto",
                    model="gpt-4o-mini",
                    temperature=self.randomness,
                )

                print("OpenAI Response:", response)  
                function_response = json.loads(response.choices[0].message.function_call.arguments)

                if "Loans" in function_response and function_response["Loans"]:
                    all_loans_info.extend(function_response["Loans"])  # Add loans to the main list
                else:
                    print("Warning: No loans extracted from this page.")

            df_loans = pd.json_normalize(all_loans_info)

            consumer_info = function_response.get('Consumer', {})
            df_consumer = pd.json_normalize(consumer_info)

            print("Consumer DataFrame:\n", df_consumer)
            print("Loans DataFrame:\n", df_loans)


            excel_filename = io.BytesIO()
            # excel_filename = "cibil_score.xlsx"

            with pd.ExcelWriter(excel_filename, engine='xlsxwriter') as writer:
                df_consumer.to_excel(writer, sheet_name='Consumer Details', index=False)
                df_loans.to_excel(writer, sheet_name='Loans', index=False)

            return {
                'file_content': excel_filename,
                'file_type': 'xlsx',
                'file_name': f"{files[0]['name']}_processed_{files[0]['media_id']}.xlsx"
            }

        except requests.RequestException as e:
            print(f"Error downloading file: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    async def run(self, query):
        return await self.execute(query)


if __name__ == '__main__':
    executor = CibilScoreExecutor(randomness=random.uniform(0.0, 1.0))
    asyncio.run(executor.execute([
        
    {
        "object_type": "post",
        "object_id": None,
        "size": 114143,
        "media_id": "00d2a8c6818211ef9b3266ac95333f55",
        "media_type": "pdf",
        "media_relation": "attachment",
        "name": "KUMAR_M_CIBIL_BC_EVATE.pdf",
        "media_url": "https://unpodbackend.s3.amazonaws.com/media/private/KUMAR_M_CIBIL_BC_EVATE_Ydtc4h9.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAUVZCV34QRNMNXSNO%2F20241003%2Fap-south-1%2Fs3%2Faws4_request&X-Amz-Date=20241003T122124Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=7b27919b77481fd825023f5dee865fe7b61bfae96e00d08c4ec9e496edd4397a",
        "url": "https://unpodbackend.s3.amazonaws.com/media/private/KUMAR_M_CIBIL_BC_EVATE_Ydtc4h9.pdf",
        "sequence_number": 0
    }

    ]))
