import json
import logging
import os
import pandas as pd
import uuid
import ast
import sys

from typing import List, Dict

import openai

from pydantic import Field
from superpilot.core.ability import Ability
from superpilot.core.ability.base import AbilityConfiguration
from superpilot.core.configuration import Config
from superpilot.core.context.schema import Context, Content, ContentType
from superpilot.core.environment import Environment
from superpilot.core.planning.strategies import SummarizerStrategy
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import SchemaModel

from qdrant_client import models,QdrantClient
from qdrant_client.http.models import PointStruct
from qdrant_client.http.models import Distance, VectorParams

client = QdrantClient(url="http://10.160.1.96:6333/") #qa - 10.160.1.96

# client.recreate_collection(
#     collection_name="test_story_v4",
#     vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
#     optimizers_config=models.OptimizersConfigDiff(indexing_threshold=0),
# )


class QdrantAbilityArguments(SchemaModel):
    """
    Container class representing a tree of questions to ask a question answer system.
    and its dependencies. Make sure every question is in the tree, and every question is asked only once.
    """

    # json_data : List[Dict] = Field(
    #     ..., description="It is list of dictionaries contain Invoice Data. Pick all returned data as it is without loosing data"
    # )
    query: str = Field(
        ..., description="It is summarized question asked by user about data, after removing parameters of previous ability,its types and return it"
    )


class QdrantAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.QdrantAbility",
        )
    )

    def __init__(
        self,
        environment: Environment,
        configuration: AbilityConfiguration = default_configuration,
        prompt_strategy: SummarizerStrategy = None,
    ):
        self._logger: logging.Logger = environment.get("logger")
        self._configuration = configuration
        self._env_config: Config = environment.get("env_config")

    @classmethod
    def description(cls) -> str:
        return """Useful when user have some questions related to data returned by previous ability the execute this ability"""

    @classmethod
    def arguments(cls) -> dict:
        args = QdrantAbilityArguments.function_schema(arguments_format=True)
        print("Arguments", args)
        return args

    async def __call__(
        self, QdrantAbilityArguments: dict, **kwargs
    ) -> Context:
        query = QdrantAbilityArguments["query"]
        print('\nQdrant Ability ------> ',query)
        with open("response_json.txt", "r") as f:
            json_file = f.read()
        # print(json_file)
        api_response = eval(json_file)

        vectors,qdrant_points = await get_vectors(api_response)
        print(len(vectors))
        print(len(qdrant_points))

        await uploadToQdrant(qdrant_points)
        # query=None
        # while True:
        #     # if query != None:
        #     #     response = get_response(query)
        #     #     query = None
        #     # elif query in ['quit', 'q', 'exit']:
        #     #     sys.exit()
        #     # else:
        #     query = str(input("Ask your query ---> "))
        #     response = get_response(query)
        #     # query = None
        #     print("Answer ---> ", response)
        #     query=None
        #     print('--------------------------------------------')
        query2 = 'How much is the total sales'
        response = await get_response(query)
        print("Answer ---> ", response,'\n')
        text = {"api_response" : [response] }
        return Context(
            [await self.get_content_item(response)]
        )

    async def get_content_item(
        self, content: str, header: dict = None, url: str = None
    ) -> Content:
        return Content.add_content_item(
            content,
            ContentType.DICT,
        )
    

def generate_story(data):
    story = f"On {data.get('Invoice_Date','N/A')}, a business transaction occurred between {data.get('Supplier_Name','Unknown Supplier Name')} and {data.get('Contact_Name','Unknown Buyer')}. The invoice, numbered {data.get('Invoice_Number','N/A')}, was for a total value of {data.get('Value','N/A')}. The transaction was categorized as {data.get('Invoice_Type','N/A')} under financial year {data.get('Financial_Year','N/A')}. The supplier's GSTIN status was {data.get('Supplier_GSTIN_Status','N/A')} and they followed a {data.get('Supplier_Return_Type','N/A')} return type. The buyer's GSTIN was {data.get('Buyer_GSTIN','N/A')} with a counter filling status of '{data.get('Counter_Filling_Status','N/A')}'."

    story += f"\n\nAdditionally, for the purchase transaction, the purchase was made from {data.get('Supplier_Name','Unknown Supplier Name')} to {data.get('Contact_Name','Unknown Buyer')}. The purchase invoice was also numbered {data.get('Purchase_Invoice_Number','NA')} for a net amount of {data.get('Purchase_Net_Amount','NA')}. The transaction was in {data.get('Purchase_Invoice_Type','NA')} category and occurred on {data.get('Purchase_Invoice_Date','NA')}. The total taxable value was {data.get('Total_Taxable_Value','NA')} and the total CGST and SGST amounted to {data.get('Purchase_Total_CGST_Amount','N/A')} and {data.get('Purchase_Total_SGST_Amount','N/A')} respectively."

    # story = story.format(**data)
    return story

async def get_vectors(data):
    qdrant_points = []
    story_data = []
    list_of_texts = []
    for list_item in data[:500]:
        text = ','.join(f"{key}: {value}" for key, value in list_item.items())
        list_of_texts.append(text)
        generated_story = generate_story(list_item)
        story_data.append(generated_story)
    
    embedding_response = openai.Embedding.create(input=story_data,model="text-embedding-ada-002")
    embedding = embedding_response['data']

    vectors= []
    for item in embedding:
        vectors.append(item['embedding'])

    for i in range(len(vectors)):
        vector_id = str(uuid.uuid4())
        qdrant_points.append(PointStruct(id=vector_id,payload=data[i],vector=vectors[i]))
    print(len(list_of_texts))
    print(len(story_data))
    print(len(qdrant_points))
    return vectors,qdrant_points

async def uploadToQdrant(qdrant_points):
    client.upsert(
        collection_name="test_story_v4",
        wait=True,
        points=qdrant_points
    )
    print("\n--------------Data Uploaded to qdrant-------------------\n")

async def get_response(query):
    query_embedding_response = openai.Embedding.create(
        input=query,
        model="text-embedding-ada-002"
    )

    query_embedding = query_embedding_response['data'][0]['embedding']

    search_result = client.search(
        collection_name="test_story_v4",
        query_vector=query_embedding,
        limit=20
    )

    prompt=""
    # for result in search_result:
    #     prompt += result.payload['text']
    for indx,result in enumerate(search_result):
        prompt += f'Invoice Number - {str(indx)} > '+str(result.payload) +'\n\n'

    # print("prompt ----------> ",prompt)

    concatenated_string = f"for the given invoice data <{prompt}> answer the following query <{query}> in short related to given data"

    # concatenated_string = " ".join([prompt,query])
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "user", "content": concatenated_string}
        ]
    )
    response = completion.choices[0].message.content

    return response


