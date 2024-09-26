import asyncio
import io
import json
import os

import PyPDF2
import boto3
import pandas as pd
from openai import OpenAI

from superpilot.core.configuration.config import get_config
from superpilot.core.context.schema import Context
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.resource.model_providers import (
    OpenAIModelName,
)
from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.examples.cibil_score.prompt import ExtractLoanInfoPrompt
from superpilot.examples.cibil_score.s3 import s3_path_split
from superpilot.examples.executor.base import BaseExecutor
from superpilot.tests.test_env_simple import get_env

client = OpenAI(
    api_key=os.environ.get('OPENAI_API_KEY')
    # other configurations...
)


class CibilScoreExecutor(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()
    context = Context()
    config = get_config()
    env = get_env({})

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.cibil_pilot = SimpleTaskPilot.create(
            ExtractLoanInfoPrompt.default_configuration,
            model_providers=self.model_providers,
            smart_model_name=OpenAIModelName.GPT4_O_MINI,
            fast_model_name=OpenAIModelName.GPT4_O_MINI,
        )

    # Helper function to download the file from an S3 URL
    def download_from_s3(self, s3_url):
        # Parse the S3 URL to get bucket and file key
        bucket_name, file_key = s3_path_split(s3_url)
        print(os.environ.get('AWS_ACCESS_KEY_ID'), os.environ.get('AWS_SECRET_ACCESS_KEY'))

        # Set up the S3 client and download the file
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
        )

        s3_object = s3.get_object(Bucket=bucket_name, Key=file_key)
        file_content = s3_object['Body'].read()  # Binary content of the file
        return file_content, file_key


    def extract_pdf_content_from_s3(self, pdf_binary_content,):
        """
        Download a PDF file from S3 and extract text content from it.
        """
        # Step 1: Download the file from S3

        # Step 2: Extract text from the PDF content
        pdf_file = io.BytesIO(pdf_binary_content)  # Convert binary to a file-like object
        reader = PyPDF2.PdfReader(pdf_file)
        content = ""

        # Iterate through each page and extract text
        for page in reader.pages:
            content += page.extract_text()

        return content

    async def execute(self, **kwargs):
        # remove dumy data
        kwargs = {
            "content": "Provide the summary of SUNIL Kumar",
            "files": [
                {
                    "object_type": "post",
                    "object_id": None,
                    "size": 114143,
                    "media_id": "873b6364791a11ef9b3266ac95333f55",
                    "media_type": "pdf",
                    "media_relation": "attachment",
                    "name": "KUMAR_M_CIBIL_BC_EVATE.pdf",
                    "media_url": "https://unpodbackend.s3.amazonaws.com/media/private/KUMAR_M_CIBIL_BC_EVATE.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAUVZCV34QRNMNXSNO%2F20240922%2Fap-south-1%2Fs3%2Faws4_request&X-Amz-Date=20240922T194032Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=f3f065adc69b7238690bf37741d5e13ab9e2961bd10b122f0cd684f90e1983f3",
                    "url": "https://unpodbackend.s3.amazonaws.com/media/private/KUMAR_M_CIBIL_BC_EVATE.pdf",
                    "sequence_number": 0
                }
            ],
            "conversation_type": "initiate",
            "source": "qa2",
            "knowledge_bases": [""],
        }

        s3_url = kwargs['files'][0]['media_url']
        # Step 1: Download file from S3 URL
        file_content, file_key = self.download_from_s3(s3_url)

        pdf_text = self.extract_pdf_content_from_s3(file_content)

        query = """
        PDF CONTENT: %s
        
        Please extract all available loan information and present it in JSON format. Ensure that no details are omitted, including but not limited to the following fields: loan ID, borrower name, loan amount, interest rate, loan term, start date, payment schedule, status, and any other relevant information. If there are nested structures or related entities, include them appropriately within the JSON.
        """ % pdf_text


        response = await self.cibil_pilot.execute(query)

        # Convert the extracted info to a DataFrame
        df_consumer = pd.json_normalize(response['Consumer'])
        df_loans = pd.json_normalize(response['Loans'])

        print(df_loans, df_consumer)

        # Save the DataFrame to Excel
        # excel_filename = io.BytesIO()
        excel_filename = "cibil_score.xlsx"

        with pd.ExcelWriter(excel_filename, engine='xlsxwriter') as writer:
            df_consumer.to_excel(writer, sheet_name='Consumer Details', index=False)
            df_loans.to_excel(writer, sheet_name='Loans', index=False)

        return f"Data extracted and saved to {excel_filename}"

    async def run(self, query):
        pass


if __name__ == '__main__':
    executor = CibilScoreExecutor()
    asyncio.run(executor.execute())
