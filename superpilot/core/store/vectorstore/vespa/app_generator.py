import json
import os.path
import time
from datetime import datetime, timedelta

import requests
from vespa.package import (
    ApplicationPackage,
    Field,
    Schema,
    Document,
    HNSW,
    RankProfile,
    Component,
    Parameter,
    FieldSet,
    GlobalPhaseRanking,
    Function,
)
from vespa.deployment import VespaDocker

from typing import Dict, Any, List, Optional

from superpilot.app.client_lib import logging
from superpilot.core.logging.logging import get_logger
from superpilot.core.store.vectorstore.vespa.configs.app_configs import VESPA_SCHEMA_PATH
from superpilot.core.store.vectorstore.vespa.utils import create_document_xml_lines, in_memory_zip_from_file_bytes, \
    fix_vespa_app_name

VESPA_DIM_REPLACEMENT_PAT = "VARIABLE_DIM"
CHUNK_REPLACEMENT_PAT = "UNPOD_CHUNK_NAME"
DOCUMENT_REPLACEMENT_PAT = "DOCUMENT_REPLACEMENT"
DATE_REPLACEMENT = "DATE_REPLACEMENT"
DOC_VESPA_PORT = "DOC_VESPA_PORT"
#
# # config server
# VESPA_CONFIG_SERVER_URL = f"http://{VESPA_CONFIG_SERVER_HOST}:{VESPA_TENANT_PORT}"
# VESPA_APPLICATION_ENDPOINT = f"{VESPA_CONFIG_SERVER_URL}/application/v2"
#
# # main search application
# VESPA_APP_CONTAINER_URL = f"http://{VESPA_HOST}:{VESPA_PORT}"
# # unpod_chunk below is defined in vespa/app_configs/schemas/unpod_chunk.sd
# DOCUMENT_ID_ENDPOINT = (
#     f"{VESPA_APP_CONTAINER_URL}/document/v1/default/{{app_name}}/docid"
# )
# SEARCH_ENDPOINT = f"{VESPA_APP_CONTAINER_URL}/search/"

_BATCH_SIZE = 128  # Specific to Vespa
_NUM_THREADS = (
    32  # since Vespa doesn't allow batching of inserts / updates, we use threads
)
# up from 500ms for now, since we've seen quite a few timeouts
# in the long term, we are looking to improve the performance of Vespa
# so that we can bring this back to default
_VESPA_TIMEOUT = "3s"
# Specific to Vespa, needed for highlighting matching keywords / section
CONTENT_SUMMARY = "content_summary"

class VespaAppGenerator:
    def __init__(
        self,
        app_name: str,
        schema_name: str = "default_doc",
        embedder_id: str = "default-embedder",
        embedder_type: str = "hugging-face-embedder",
        transformer_model_url: Optional[str] = None,
        tokenizer_model_url: Optional[str] = None,
    ):
        """
        Initializes the Vespa Application Generator.

        :param app_name: Name of the Vespa application.
        :param schema_name: Name of the document schema.
        :param embedder_id: ID for the embedding component.
        :param embedder_type: Type of the embedding component.
        :param transformer_model_url: URL to the transformer model.
        :param tokenizer_model_url: URL to the tokenizer model.
        """
        self.app_name = app_name
        self.schema_name = schema_name
        self.secondary_schema_name = f"{schema_name}_s3c04d0ry"
        self.embedder_id = embedder_id
        self.embedder_type = embedder_type
        self.transformer_model_url = transformer_model_url or ""
        self.tokenizer_model_url = tokenizer_model_url or ""
        self.fields: List[Field] = []
        self.fieldsets: List[FieldSet] = []
        self.rank_profiles: List[RankProfile] = []
        self.components: List[Component] = []
        self.embedding_field_added = False
        self.logger = get_logger(__name__)

    def map_json_type_to_vespa(self, json_type: str) -> str:
        """
        Maps JSON schema types to Vespa field types.

        :param json_type: The JSON type as a string.
        :return: Corresponding Vespa field type.
        """
        mapping = {
            "string": "string",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "date": "date",
            # Add more mappings as needed
        }
        return mapping.get(json_type, "string")  # Default to string

    def add_field(
        self,
        name: str,
        json_type: str,
        indexing: Optional[List[str]] = None,
        is_document_field: bool = True,
        tensor_dimensions: Optional[str] = None,
        ann_distance_metric: Optional[str] = None,
    ):
        """
        Adds a field to the schema based on JSON type and additional parameters.

        :param name: Field name.
        :param json_type: JSON field type.
        :param indexing: List of indexing options.
        :param is_document_field: Whether the field is part of the document.
        :param tensor_dimensions: Tensor dimensions if the field is a tensor.
        :param ann_distance_metric: Distance metric for ANN fields.
        """
        vespa_type = self.map_json_type_to_vespa(json_type)
        field_kwargs: Dict[str, Any] = {
            "name": name,
            "type": vespa_type,
            "is_document_field": is_document_field,
        }

        if indexing:
            field_kwargs["indexing"] = indexing

        if tensor_dimensions:
            field_kwargs["type"] = f"tensor<float>({tensor_dimensions})"
            if ann_distance_metric:
                field_kwargs["ann"] = HNSW(distance_metric=ann_distance_metric)
            field_kwargs["is_document_field"] = False  # Typically tensors are attributes

        self.fields.append(Field(**field_kwargs))

    def parse_json_schema(self, json_schema: Dict[str, Any]):
        """
        Parses the JSON schema and populates the fields.

        :param json_schema: The JSON schema as a dictionary.
        """
        properties = json_schema.get("properties", {})
        for field_name, attributes in properties.items():
            json_type = attributes.get("type", "string")
            # Determine indexing options based on type
            indexing = ["summary"] if json_type == "string" else []
            # Example: add 'index' for searchable fields
            if json_type in ["string", "integer", "float", "date"]:
                indexing.append("index")
                indexing.append("summary")

            # Special handling for specific fields if needed
            if field_name.lower() in ["title", "body", "name", "content", "text", "description", "summary"]:
                indexing.append("enable-bm25")

            # Add the field
            self.add_field(
                name=field_name,
                json_type=json_type,
                indexing=indexing,
                is_document_field=True,
            )

        # Optionally, add a default fieldset
        # For simplicity, include all string fields in the default fieldset
        string_fields = [f.name for f in self.fields if f.type == "string"]
        if string_fields:
            self.fieldsets.append(FieldSet(name="default", fields=string_fields))

    def add_embedding_field(
        self,
        name: str = "embedding",
        tensor_dimensions: str = "x[384]",
        distance_metric: str = "angular",
    ):
        """
        Adds an embedding tensor field to the schema.

        :param name: Name of the embedding field.
        :param tensor_dimensions: Dimensions of the tensor.
        :param distance_metric: Distance metric for ANN.
        """
        if not self.embedding_field_added:
            input_text_line = self.generate_input_text()
            self.fields.append(
                Field(
                    name=name,
                    type=f"tensor<float>({tensor_dimensions})",
                    indexing=[
                        input_text_line,
                        "embed",
                        "index",
                        "attribute",
                    ],
                    ann=HNSW(distance_metric=distance_metric),
                    is_document_field=False,
                )
            )
            self.embedding_field_added = True

    def get_text_fields(self, max_fields: int = 3) -> List[str]:
        """
        Get a list of field names that are of type 'string'.

        :return: List of string field names.
        """
        text_fields = [f.name for f in self.fields if f.type == "string"]
        return text_fields[:max_fields]

    def generate_input_text(self, max_fields: int = 3) -> str:
        """
        Generate a concatenation of up to 3 text-based fields.

        :param fields: List of available fields.
        :param max_fields: Maximum number of text fields to concatenate.
        :return: A string representing the concatenated fields.
        """
        selected_fields = self.get_text_fields(max_fields)
        # Generate the concatenated input
        input_text = " . \" \" . ".join([f"input {field}" for field in selected_fields])

        return input_text

    def bm25_fields(self, max_fields: int = 3) -> str:
        """
        Generate BM25 fields from a list of fields.

        :param max_fields:
        :return: A string representing the BM25 fields.
        """
        selected_fields = self.get_text_fields(max_fields)
        bm25_fields = " + ".join([f"bm25({field})" for field in selected_fields])
        return bm25_fields

    def add_rank_profiles(self):
        """
        Adds default rank profiles: bm25, semantic, and fusion.
        """
        bm25_fields = self.bm25_fields()
        # BM25 Rank Profile
        bm25_profile = RankProfile(
            name="bm25",
            inputs=[("query(q)", "tensor<float>(x[384])")],
            functions=[
                Function(name="bm25sum", expression=bm25_fields)
            ],
            first_phase="bm25sum",
        )
        self.rank_profiles.append(bm25_profile)

        # Semantic Rank Profile
        semantic_profile = RankProfile(
            name="semantic",
            inputs=[("query(q)", "tensor<float>(x[384])")],
            first_phase="closeness(field, embedding)",
        )
        self.rank_profiles.append(semantic_profile)

        # Fusion Rank Profile
        fusion_profile = RankProfile(
            name="fusion",
            inherits="bm25",
            inputs=[("query(q)", "tensor<float>(x[384])")],
            first_phase="closeness(field, embedding)",
            global_phase=GlobalPhaseRanking(
                expression="reciprocal_rank_fusion(bm25sum, closeness(field, embedding))",
                rerank_count=1000,
            ),
        )
        self.rank_profiles.append(fusion_profile)

    def add_components(
        self,
        embedder_id: Optional[str] = None,
        embedder_type: Optional[str] = None,
        transformer_model_url: Optional[str] = None,
        tokenizer_model_url: Optional[str] = None,
    ):
        """
        Adds components to the application package, such as the embedder.

        :param embedder_id: ID for the embedder component.
        :param embedder_type: Type of the embedder component.
        :param transformer_model_url: URL to the transformer model.
        :param tokenizer_model_url: URL to the tokenizer model.
        """
        component = Component(
            id=embedder_id or self.embedder_id,
            type=embedder_type or self.embedder_type,
            parameters=[
                Parameter(
                    "transformer-model",
                    {"url": transformer_model_url or self.transformer_model_url},
                ),
                Parameter(
                    "tokenizer-model",
                    {"url": tokenizer_model_url or self.tokenizer_model_url},
                ),
            ],
        )
        self.components.append(component)

    def generate_application_package(self, json_schema: Dict[str, Any]) -> ApplicationPackage:
        """
        Generates the Vespa ApplicationPackage based on the provided JSON schema.

        :param json_schema: The JSON schema as a dictionary.
        :return: An instance of ApplicationPackage.
        """
        # Parse JSON schema to populate fields
        self.parse_json_schema(json_schema)

        # Optionally, add embedding field if needed
        self.add_embedding_field()

        # Add default rank profiles
        self.add_rank_profiles()

        # Add components (e.g., embedder)
        self.add_components()

        # Define the document
        document = Document(fields=self.fields)

        # Define the schema
        schema = Schema(
            name=self.schema_name,
            document=document,
            fieldsets=self.fieldsets,
            rank_profiles=self.rank_profiles,
        )

        app_name = fix_vespa_app_name(self.app_name)
        # Create the application package
        package = ApplicationPackage(
            name=app_name,
            schema=[schema],
            components=self.components,
        )

        return package

    def deploy_app_zip(self,
                   host: Optional[str] = "localhost",
                   port: Optional[int] = 19071,
                   app_zip_content: Optional[bytes] = None,
                   **kwargs) -> Any:
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
        # # config server
        VESPA_CONFIG_SERVER_URL = f"http://{host}:{port}"
        VESPA_APPLICATION_ENDPOINT = f"{VESPA_CONFIG_SERVER_URL}/application/v2"
        # Define deployment URL for Vespa.ai
        deploy_url = f"{VESPA_APPLICATION_ENDPOINT}/tenant/default/prepareandactivate"
        print("deploy_url", deploy_url)
        self.logger.debug(f"Sending Vespa zip to {deploy_url}")

        # Prepare in-memory ZIP file containing the files for deployment
        # zip_file = in_memory_zip_from_file_bytes(app_zip_content)

        # Set headers and make the POST request to deploy to Vespa.ai
        headers = {"Content-Type": "application/zip"}
        response = requests.post(deploy_url, headers=headers, data=app_zip_content)

        # Check for a successful response, otherwise raise an error
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to prepare Vespa index. Response: {response.text}"
            )

        # Assuming the response contains indexed objects, we return them as a set
        return True

    def deploy_app(self,
                   host: Optional[str] = "localhost",
                   port: Optional[int] = 19071,
                   app_path: Optional[str] = VESPA_SCHEMA_PATH,
                   **kwargs) -> Any:
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
        # # config server
        VESPA_CONFIG_SERVER_URL = f"http://{host}:{port}"
        VESPA_APPLICATION_ENDPOINT = f"{VESPA_CONFIG_SERVER_URL}/application/v2"
        # Define deployment URL for Vespa.ai
        deploy_url = f"{VESPA_APPLICATION_ENDPOINT}/tenant/default/prepareandactivate"
        print("deploy_url", deploy_url)
        self.logger.debug(f"Sending Vespa zip to {deploy_url}")

        # Prepare paths for necessary Vespa schema and configuration files
        vespa_schema_path = app_path
        schema_file = os.path.join(vespa_schema_path, "schemas", f"{self.schema_name}.sd")
        services_file = os.path.join(vespa_schema_path, "services.xml")
        overrides_file = os.path.join(vespa_schema_path, "validation-overrides.xml")

        # Read the services XML template
        with open(services_file, "r") as services_f:
            services_template = services_f.read()

        # Create document lines based on schema names
        schema_names = [self.schema_name, self.secondary_schema_name]
        doc_lines = create_document_xml_lines(schema_names)

        # Replace placeholders in the services template with the document schema
        services = services_template.replace(DOCUMENT_REPLACEMENT_PAT, doc_lines)

        # Read the overrides XML template
        if not os.path.exists(overrides_file):
            base_path = os.path.dirname(os.path.dirname(vespa_schema_path))
            print("Base Path",base_path)
            overrides_file = "/Users/zestgeek-29/Desktop/Work/superpilot/superpilot/core/store/vectorstore/vespa/app_config/validation-overrides.xml"
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
            CHUNK_REPLACEMENT_PAT, self.schema_name
        ).replace(VESPA_DIM_REPLACEMENT_PAT, str(kwargs.get("index_embedding_dim", 128)))  # Default embedding dimension is 128

        zip_dict[f"schemas/{schema_names[0]}.sd"] = schema.encode("utf-8")

        # If there's a secondary index, process that schema too
        if self.secondary_schema_name:
            upcoming_schema = schema_template.replace(
                CHUNK_REPLACEMENT_PAT, self.secondary_schema_name
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
        return True

    def deploy_on_docker(self, app_package: ApplicationPackage, app_path: str):
        """
        Deploys the application package to Vespa using VespaDocker.

        Args:
        - app_package: Application package to deploy.
        - disk_folder: Folder to store the application package.

        Returns:
        - VespaDocker: VespaDocker instance.
        """
        # Write the application package to disk
        app_package.write_files(app_path)

        # Deploy the application package to Vespa using VespaDocker
        vespa_docker = VespaDocker(port=8080)
        app = vespa_docker.deploy(application_package=app_package)

        # Wait for Vespa to be ready
        vespa_docker.wait_for_ready()

        return app

    def generate_app(self, json_schema, app_path="vespa"):
        app_package = self.generate_application_package(json_schema)
        app_path = os.path.join(app_path, self.app_name)
        app_package.to_files(app_path)
        return app_package

    def deploy(self, app_path="vespa"):
        # ZIP Deployment
        # zip_file = app_package.to_zip()
        # self.deploy_app_zip(app_zip_content=zip_file)
        wait_time = 5
        for attempt in range(5):
            try:
                deployment_result = self.deploy_app(app_path=app_path)
                break
            except Exception as ex:
                self.logger.info(f"Waiting on Vespa, retrying in {wait_time} seconds...", ex)
                time.sleep(wait_time)
                deployment_result = None
        print("Done!")
        return deployment_result


    @classmethod
    def factory(cls,
                app_name,
                schema_name="default_doc",
                transformer_model_url=None,
                tokenizer_model_url=None):
        generator = cls(
            app_name=app_name,
            schema_name=schema_name,
            transformer_model_url=transformer_model_url or "https://github.com/vespa-engine/sample-apps/raw/master/simple-semantic-search/model/e5-small-v2-int8.onnx",
            tokenizer_model_url=tokenizer_model_url or "https://raw.githubusercontent.com/vespa-engine/sample-apps/master/simple-semantic-search/model/tokenizer.json"
        )
        return generator






