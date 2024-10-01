from typing import Any
from superpilot.core.store.base import VectorStoreBase
from superpilot.core.store.schema import Object
import concurrent.futures
import io
import json
import os
import string
import time
import zipfile
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from typing import BinaryIO
from typing import cast
from datetime import datetime, timedelta
from superpilot.core.store.vectorstore.vespa.index_utils import _clean_chunk_id_copy,_create_document_xml_lines, in_memory_zip_from_file_bytes,_clear_and_index_vespa_chunks

import httpx
import requests

from retry import retry

from superpilot.core.store.vectorstore.vespa.configs.app_configs import LOG_VESPA_TIMING_INFORMATION
from superpilot.core.store.vectorstore.vespa.configs.app_configs import VESPA_CONFIG_SERVER_HOST
from superpilot.core.store.vectorstore.vespa.configs.app_configs import VESPA_HOST
from superpilot.core.store.vectorstore.vespa.configs.app_configs import VESPA_PORT
from superpilot.core.store.vectorstore.vespa.configs.app_configs import VESPA_TENANT_PORT
from superpilot.core.store.vectorstore.vespa.configs.app_configs import VESPA_SCHEMA_PATH 
from superpilot.core.store.vectorstore.vespa.configs.chat_configs import DOC_TIME_DECAY
from superpilot.core.store.vectorstore.vespa.configs.chat_configs import EDIT_KEYWORD_QUERY
from superpilot.core.store.vectorstore.vespa.configs.chat_configs import HYBRID_ALPHA
from superpilot.core.store.vectorstore.vespa.configs.chat_configs import NUM_RETURNED_HITS
from superpilot.core.store.vectorstore.vespa.configs.chat_configs import TITLE_CONTENT_RATIO
from superpilot.core.store.vectorstore.vespa.configs.constants import ACCESS_CONTROL_LIST
from superpilot.core.store.vectorstore.vespa.configs.constants import UNPOD_HUB_ID
from superpilot.core.store.vectorstore.vespa.configs.constants import UNPOD_KN_TOKEN
from superpilot.core.store.vectorstore.vespa.configs.constants import BLURB
from superpilot.core.store.vectorstore.vespa.configs.constants import BOOST
from superpilot.core.store.vectorstore.vespa.configs.constants import CHUNK_ID
from superpilot.core.store.vectorstore.vespa.configs.constants import CONTENT
from superpilot.core.store.vectorstore.vespa.configs.constants import DOC_UPDATED_AT
from superpilot.core.store.vectorstore.vespa.configs.constants import DOCUMENT_ID
from superpilot.core.store.vectorstore.vespa.configs.constants import DOCUMENT_SETS
from superpilot.core.store.vectorstore.vespa.configs.constants import EMBEDDINGS
from superpilot.core.store.vectorstore.vespa.configs.constants import HIDDEN
from superpilot.core.store.vectorstore.vespa.configs.constants import INDEX_SEPARATOR
from superpilot.core.store.vectorstore.vespa.configs.constants import METADATA
from superpilot.core.store.vectorstore.vespa.configs.constants import METADATA_LIST
from superpilot.core.store.vectorstore.vespa.configs.constants import PRIMARY_OWNERS
from superpilot.core.store.vectorstore.vespa.configs.constants import RECENCY_BIAS
from superpilot.core.store.vectorstore.vespa.configs.constants import SECONDARY_OWNERS
from superpilot.core.store.vectorstore.vespa.configs.constants import SECTION_CONTINUATION
from superpilot.core.store.vectorstore.vespa.configs.constants import SEMANTIC_IDENTIFIER
from superpilot.core.store.vectorstore.vespa.configs.constants import SKIP_TITLE_EMBEDDING
from superpilot.core.store.vectorstore.vespa.configs.constants import SOURCE_LINKS
from superpilot.core.store.vectorstore.vespa.configs.constants import SOURCE_TYPE
from superpilot.core.store.vectorstore.vespa.configs.constants import TITLE
from superpilot.core.store.vectorstore.vespa.configs.constants import TITLE_EMBEDDING
from superpilot.core.store.vectorstore.vespa.configs.constants import TITLE_SEPARATOR
from superpilot.core.store.vectorstore.vespa.configs.model_configs import SEARCH_DISTANCE_CUTOFF
import random
#import setup_logger
from superpilot.core.logging.logging import get_logger
logger=get_logger(__name__)


CONTENT_SUMMARY=None
class VespaStore(VectorStoreBase):
    yql_base = (
        f"select "
        f"documentid, "
        f"{DOCUMENT_ID}, "
        f"{CHUNK_ID}, "
        f"{BLURB}, "
        f"{CONTENT}, "
        f"{SOURCE_TYPE}, "
        f"{SOURCE_LINKS}, "
        f"{SEMANTIC_IDENTIFIER}, "
        f"{SECTION_CONTINUATION}, "
        f"{BOOST}, "
        f"{HIDDEN}, "
        f"{DOC_UPDATED_AT}, "
        f"{PRIMARY_OWNERS}, "
        f"{SECONDARY_OWNERS}, "
        f"{METADATA}, "
        f"{CONTENT_SUMMARY} "
        f"from {{index_name}} where "
    )
    def __init__(self, index_name: str, secondary_index_name: str | None) -> None:
        self.index_name = index_name
        self.secondary_index_name = secondary_index_name

    def create_index(self, schema_file_path, services_file_path, overrides_file_path, **kwargs: Any) -> set[Object]:
        """
        Creates and deploys the index schema on Vespa.ai engine.

        Args:
        - schema_file_path: Path to the schema file.
        - services_file_path: Path to the services file.
        - overrides_file_path: Path to the validation-overrides file.
        - kwargs: Additional arguments.

        Returns:
        - Set of Object that represents the indexed data.
        """

        # Define deployment URL for Vespa.ai
        deploy_url = f"{VESPA_APPLICATION_ENDPOINT}/tenant/default/prepareandactivate"
        print("deploy_url", deploy_url)
        logger.debug(f"Sending Vespa zip to {deploy_url}")

        # Prepare paths for necessary Vespa schema and configuration files
        vespa_schema_path = VESPA_SCHEMA_PATH
        schema_file = schema_file_path
        services_file = services_file_path
        overrides_file = overrides_file_path

        # Read the services XML template
        with open(services_file, "r") as services_f:
            services_template = services_f.read()

        # Create document lines based on schema names
        schema_names = [self.index_name, self.secondary_index_name]
        doc_lines = _create_document_xml_lines(schema_names)

        # Replace placeholders in the services template with the document schema
        services = services_template.replace(DOCUMENT_REPLACEMENT_PAT, doc_lines)

        # Read the overrides XML template
        with open(overrides_file, "r") as overrides_f:
            overrides_template = overrides_f.read()

        # Vespa requires a validation override to erase data including the indices no longer in use
        now = datetime.now()
        date_in_7_days = now + timedelta(days=7)
        formatted_date = date_in_7_days.strftime("%Y-%m-%d")

        # Replace the date placeholder with the dynamically computed date
        overrides = overrides_template.replace(DATE_REPLACEMENT, formatted_date)

        # Create the ZIP dictionary to store files that will be uploaded
        zip_dict = {
            "services.xml": services.encode("utf-8"),
            "validation-overrides.xml": overrides.encode("utf-8"),
        }

        # Read and process the schema file
        with open(schema_file, "r") as schema_f:
            schema_template = schema_f.read()

        # Replace placeholders in the schema template
        schema = schema_template.replace(
            CHUNK_REPLACEMENT_PAT, self.index_name
        ).replace(VESPA_DIM_REPLACEMENT_PAT, str(kwargs.get("index_embedding_dim", 128)))  # Default embedding dimension is 128

        zip_dict[f"schemas/{schema_names[0]}.sd"] = schema.encode("utf-8")

        # If there's a secondary index, process that schema too
        if self.secondary_index_name:
            upcoming_schema = schema_template.replace(
                CHUNK_REPLACEMENT_PAT, self.secondary_index_name
            ).replace(VESPA_DIM_REPLACEMENT_PAT, str(kwargs.get("secondary_index_embedding_dim", 128)))
            zip_dict[f"schemas/{schema_names[1]}.sd"] = upcoming_schema.encode("utf-8")

        # Prepare in-memory ZIP file containing the files for deployment
        zip_file = in_memory_zip_from_file_bytes(zip_dict)

        # Set headers and make the POST request to deploy to Vespa.ai
        headers = {"Content-Type": "application/zip"}
        response = requests.post(deploy_url, headers=headers, data=zip_file)

        # Check for a successful response, otherwise raise an error
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to prepare Vespa index. Response: {response.text}"
            )

        # Assuming the response contains indexed objects, we return them as a set
        return set([Object(**kwargs)])


    def get(self, object_id):
        # Sample implementation for getting an object by id
        for obj in self.indexed_data:
            if obj.obj_id == object_id:
                return obj
        return None

    def get_all(self):
        # Return all indexed objects
        return list(self.indexed_data)
    

    def _check_if_reindexing_needed(cleaned_chunks: list[Object]) -> bool:
        """
        Determines whether the index schema needs to be recreated based on the chunks' structure.

        Args:
        - cleaned_chunks: A list of cleaned document chunks.

        Returns:
        - A boolean indicating if reindexing is required.
        """
    
    # Example criteria for reindexing: Checking if a new field exists in the chunk structure
    # or if the chunk structure has missing fields or changed.
    
        required_fields = {"chunk_id", "content", "metadata", "embedding_dim"}
        
        for chunk in cleaned_chunks:
            # Assuming `chunk` has a dictionary-like structure or attribute access
            chunk_fields = set(chunk.__dict__.keys())  # Extract fields present in the chunk
            
            # Check if required fields are missing in this chunk or new fields are present
            if not required_fields.issubset(chunk_fields):
                # Required fields are missing, meaning reindexing might be needed
                return True
            
            # Optional: Check for other conditions that could necessitate reindexing,
            # such as changes in data structure, versioning, or content size.
            if getattr(chunk, "schema_version", None) != EXPECTED_SCHEMA_VERSION:
                return True

        # If none of the conditions are met, return False (no reindexing needed)
        return False

    """
    def index(self, chunks: list[Object]) -> set[Object]:
        
        # Indexes a list of document chunks, ensuring no duplicates.
        
        cleaned_chunks = [_clean_chunk_id_copy(chunk) for chunk in chunks]

        # Step 2: Define a set to hold all indexed objects (chunks and mini chunks)
        indexed_objects = set()

        # Step 3: Process each chunk to handle mini chunks and index them
        for chunk in cleaned_chunks:
            # Check if the chunk contains mini chunks
            if hasattr(chunk, "mini_chunks"):
                for mini_chunk in chunk.mini_chunks:
                    # Index each mini chunk
                    indexed_objects.add(_clear_and_index_vespa_chunks([mini_chunk], self.index_name))
            else:
                # Index the main chunk if no mini chunks are present
                indexed_objects.add(_clear_and_index_vespa_chunks([chunk], self.index_name))
        
        # Step 4: Check if indexing schema needs to be updated (e.g., new document structure)
        if _check_if_reindexing_needed(cleaned_chunks):
            # Recreate or update the index by calling create_index
            self.create_index(schema_file_path="path_to_schema", 
                              services_file_path="path_to_services", 
                              overrides_file_path="path_to_overrides")

        # Step 5: Return the set of indexed objects
        return indexed_objects

    

    def index(self, chunks: list[Object]) -> dict:
    # Initialize the result dictionary
        result = {}

        # Iterate through the list of Object instances
          # Second half of words

            # Add the mini objects to the result dictionary
        result[idx] = {
                1: mini_obj1,  # Mini object 01
                2: mini_obj2   # Mini object 02
            }
        
        # Return the resulting dictionary
        return result
    """

    def index(self, chunks: list[Object]) -> dict:
    # Initialize the result dictionary
        result = {}

        # Iterate through the list of Object instances
        for idx, obj in enumerate(chunks):
            # Split the content of the object into words
            words = obj.content.split()
            
            # Determine the midpoint to split the words into two halves
            mid_point = len(words) // 2
            
            # Create two mini objects based on word count
            mini_obj1 = ' '.join(words[:mid_point])  # First half of words
            mini_obj2 = ' '.join(words[mid_point:])

            # Create two new Object instances with the same properties, but different content
            mini_obj1 = Object(
                blurb=obj.blurb,
                #id=f"{obj.id}_1",  # Unique ID for mini object 1
                ref_id=obj.ref_id,
                obj_id=obj.obj_id + "_1",  # Add suffix to distinguish mini objects
                content=mini_obj1,
                source=obj.source,
                privacy=obj.privacy,
                embeddings=obj.embeddings,
                metadata=obj.metadata,
                type=obj.type
            )

            mini_obj2 = Object(
                blurb=obj.blurb,
                #id=f"{obj.id}_2",  # Unique ID for mini object 2
                ref_id=obj.ref_id,
                obj_id=obj.obj_id + "_2",  # Add suffix to distinguish mini objects
                content=mini_obj2,
                source=obj.source,
                privacy=obj.privacy,
                embeddings=obj.embeddings,
                metadata=obj.metadata,
                type=obj.type
            )

            # Add the mini objects to the result dictionary
            result[idx] = {
                1: mini_obj1,  # Mini object 01
                2: mini_obj2   # Mini object 02
            }

        # Return the resulting dictionary
        return result





    def update(self, object_id, data):
        pass

    def delete(self, object_id):
        pass

    def history(self, object_id):
        pass

    




