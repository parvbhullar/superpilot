from typing import Any
from superpilot.core.store.base import VectorStoreBase
from superpilot.core.store.schema import Object
from typing import Any

from superpilot.core.store.vectorstore.vespa.app_generator import VespaAppGenerator
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


class VespaStore(VectorStoreBase):
    def __init__(self, index_name: str, secondary_index_name: str | None) -> None:
        self.index_name = index_name
        self.secondary_index_name = secondary_index_name

    def create_index(self,
                     app_name,
                     schema_name,
                     app_path,
                     schema=None,
                     **kwargs: Any
                     ) -> bool:
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
        app_generator = VespaAppGenerator.factory(app_name=app_name, schema_name=schema_name)
        if schema:
            app_generator.generate_app(json_schema=schema)
        response = app_generator.deploy(app_path=app_path)

        return True


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


    def index(self, chunks: list[Object]) -> set[Object]:
        """
        Indexes a list of document chunks, ensuring no duplicates.
        """
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





'''
    def update(self, object_id, data):
        pass

    def delete(self, object_id):
        pass

    def history(self, object_id):
        pass

    def index(self, chunks: list[Object]) -> set[Object]:
        pass

        '''

