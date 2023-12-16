import json
import logging
import os
import pandas as pd

import requests
from pydantic import Field
from superpilot.core.ability import Ability
from superpilot.core.ability.base import AbilityConfiguration
from superpilot.core.configuration import Config
from superpilot.core.context.schema import Context, Content, ContentType
from superpilot.core.environment import Environment
from superpilot.core.planning.strategies import SummarizerStrategy
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import SchemaModel
from superpilot.examples.rag.abilities.constants import API_FULLTEXT_MAPPER


class RecoAbilityArguments(SchemaModel):
    """
    Container class representing a tree of questions to ask a question answer system.
    and its dependencies. Make sure every question is in the tree, and every question is asked only once.
    """

    buyer_gstin: str = Field(
        ..., description="Buyer GSTIN or gst number for reco api "
    )
    f_year: str = Field(
        ..., description="Financial Year for the API call"
    )
    reco_type: str = Field(
        ..., description="Type of Reconciliation. If in input GSTR2A or 2a persent return it as '2A-PR' or if GSTR2B or 2b, return it as '2B-PR'."
    ) 
    # query: str = Field(
    #     ..., description=f"whole query as it is without {buyer_gstin},{f_year}, {reco_type}"
    # )  


class RecoAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.RecoAbility",
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
        return """
            Useful when you want to get data regarding reconciliation i.e reco API.
            You should trigger the reco api. Don't give the explaination, just give the api's response as it is.
            Once the Successful available in reco api response, your task is done"""

    @classmethod
    def arguments(cls) -> dict:
        args = RecoAbilityArguments.function_schema(arguments_format=True)
        print("\nArguments", args)
        return args

    async def __call__(
        self, RecoAbilityArguments: dict, **kwargs
    ) -> Context:
        buyer_gstin = RecoAbilityArguments["buyer_gstin"]
        f_year = RecoAbilityArguments["f_year"]
        reco_type = RecoAbilityArguments["reco_type"]
        # query = RecoAbilityArguments["query"]
        print(self.name(), '---->', buyer_gstin, f_year,reco_type)

        response = await reco_data_extract(buyer_gstin=buyer_gstin,f_year=f_year,reco_type=reco_type)
        # print(response.json())

        if isinstance(response.json()['data'], type([])):
            # If data is less than 10k
            # Normalize the nested python dict

            api_normalize_response = await clean_list_of_dicts(response.json()['data'], API_FULLTEXT_MAPPER)

            # Saving data fro Qdrant Ability
            with open('response_json.txt', 'w') as f:
                f.write(str(api_normalize_response))
            # Save the updated dataframe to a new CSV file for SQL Ability
            df = await json_to_df(api_normalize_response)
            df.to_csv('response.csv', index=False)         
    
        else:
            print('Reco Records are more than 10K or No data in Response')
            return {'error': 'Reco Records are more than 10K or No data in Response'}
        
        return Context().add_content("Reco API Response is saved in response_json.txt and response.csv")

    async def get_content_item(
        self, content: str, header: dict = None, url: str = None
    ) -> Content:
        return Content.add_content_item(
            content,
            ContentType.DICT,
            # source=url,
            # content_metadata={"header": header},
        )

# async def normalize_json(lists):
        
#         final_data = []
#         new_list = []
#         for lis in lists:
#             new_data = dict()
#             for key, value in lis.items():
#                 if not isinstance(value, dict):
#                     new_data[key] = value
#                 else:
#                     for k, v in value.items():
#                         new_data[key + "_" + k] = v
#             new_list.append(new_data)

#         for item in new_list:
#             item_dict = {}
#             for key, value in item.items():
#                 if key in API_FULLTEXT_MAPPER.keys():
#                     item_dict[API_FULLTEXT_MAPPER[key]] = value
#                 else:
#                     item_dict[key] = value
#             final_data.append(item_dict)
#         return final_data


async def reco_data_extract(buyer_gstin, reco_type, f_year):
    tok_response = requests.post(
        url="https://qa-arapback.mastersindia-einv.com/api/v1/token-auth/",
        data={"username": os.environ.get("MI_USERNAME"), "password": os.environ.get("MI_PASSWORD")},
    )

    response = requests.get(
        url="https://qa-arapback.mastersindia-einv.com/api/v1/saas-apis/recoapi/?buyer_gstin="
        + buyer_gstin
        + "&reco_type="
        + reco_type
        + "&f_year="
        + f_year,
        headers={
            "Authorization": f"JWT {tok_response.json()['token']}",
            "Productid": "enterprises",
            "GSTIN": buyer_gstin,
        },
    )

    if response.status_code != 200:
        print(
            f"something went wrong from the reco api side with status code {response.status_code}"
        )
    return response

async def json_to_df(data):
    if isinstance(data, type([])):
        main_df = pd.DataFrame(data)
        main_df = main_df.fillna('')
        return main_df
    elif isinstance(data, type({})):
        main_df = pd.DataFrame([data])
        main_df = main_df.fillna('')
        return main_df
    else : 
        return pd.DataFrame([])
    
async def clean_data_with_specific_mapping(single_data, mapping, parent_key=''):
    cleaned_data = {}
    for key, value in single_data.items():
        new_key = mapping.get(key, key)
        new_key = f"{parent_key}_{new_key}" if parent_key else new_key

        if isinstance(value, dict):
            cleaned_data.update(await clean_data_with_specific_mapping(value, mapping, new_key))  # Recursively clean nested dictionaries

        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    cleaned_data.update(await clean_data_with_specific_mapping(item, mapping, f"{new_key}_{i}"))
                else:
                    cleaned_data[f"{new_key}_{i}"] = item

        else:
            cleaned_data[new_key] = value

    return cleaned_data

async def clean_list_of_dicts(list_of_dicts, mapping):
    cleaned_data_list = []
    for data_dict in list_of_dicts:
        cleaned_data = await clean_data_with_specific_mapping(data_dict, mapping)
        cleaned_data_list.append(cleaned_data)
    return cleaned_data_list