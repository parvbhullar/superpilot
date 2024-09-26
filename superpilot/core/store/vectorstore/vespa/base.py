from typing import Any

from superpilot.core.store.base import VectorStoreBase
from superpilot.core.store.schema import Object



class VespaStore(VectorStoreBase):
    def __init__(self):
        self.indexed_data = set()

    def create_index(self, schema_file_path, services_file, overrides_file, **kwargs: Any) -> set[Object]:
        deploy_url = f"{VESPA_APPLICATION_ENDPOINT}/tenant/default/prepareandactivate"
        print("deploy_url", deploy_url)
        logger.debug(f"Sending Vespa zip to {deploy_url}")

        # vespa_schema_path = os.path.join(
        #     os.getcwd(), "unpod", "document_index", "vespa", "app_config"
        # )
        vespa_schema_path = VESPA_SCHEMA_PATH
        schema_file = os.path.join(vespa_schema_path, "schemas", "unpod_chunk.sd")
        services_file = os.path.join(vespa_schema_path, "services.xml")
        overrides_file = os.path.join(vespa_schema_path, "validation-overrides.xml")

        with open(services_file, "r") as services_f:
            services_template = services_f.read()

        schema_names = [self.index_name, self.secondary_index_name]

        doc_lines = _create_document_xml_lines(schema_names)
        services = services_template.replace(DOCUMENT_REPLACEMENT_PAT, doc_lines)
        # services = services.replace(DOC_VESPA_PORT, VESPA_PORT)

        with open(overrides_file, "r") as overrides_f:
            overrides_template = overrides_f.read()

        # Vespa requires an override to erase data including the indices we're no longer using
        # It also has a 30 day cap from current so we set it to 7 dynamically
        now = datetime.now()
        date_in_7_days = now + timedelta(days=7)
        formatted_date = date_in_7_days.strftime("%Y-%m-%d")

        overrides = overrides_template.replace(DATE_REPLACEMENT, formatted_date)

        zip_dict = {
            "services.xml": services.encode("utf-8"),
            "validation-overrides.xml": overrides.encode("utf-8"),
        }

        with open(schema_file, "r") as schema_f:
            schema_template = schema_f.read()

        schema = schema_template.replace(
            UNPOD_CHUNK_REPLACEMENT_PAT, self.index_name
        ).replace(VESPA_DIM_REPLACEMENT_PAT, str(index_embedding_dim))
        zip_dict[f"schemas/{schema_names[0]}.sd"] = schema.encode("utf-8")

        if self.secondary_index_name:
            upcoming_schema = schema_template.replace(
                UNPOD_CHUNK_REPLACEMENT_PAT, self.secondary_index_name
            ).replace(VESPA_DIM_REPLACEMENT_PAT, str(secondary_index_embedding_dim))
            zip_dict[f"schemas/{schema_names[1]}.sd"] = upcoming_schema.encode("utf-8")

        # for file in zip_dict.keys():
        #     logger.debug(f"File in zip: {file}")
        #     data = zip_dict[file]
        #     if "schemas" in file:
        #         os.makedirs(os.path.dirname(file), exist_ok=True)
        #     with open(file, "wb") as f:
        #         f.write(data)

        zip_file = in_memory_zip_from_file_bytes(zip_dict)

        headers = {"Content-Type": "application/zip"}
        response = requests.post(deploy_url, headers=headers, data=zip_file)
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to prepare Vespa Unpod Index. Response: {response.text}"
            )


def get(self, object_id):
        # Sample implementation for getting an object by id
        for obj in self.indexed_data:
            if obj.obj_id == object_id:
                return obj
        return None

    def get_all(self):
        # Return all indexed objects
        return list(self.indexed_data)

    def index(self, chunks: list[Object]) -> set[Object]:
        """
        Indexes a list of document chunks, ensuring no duplicates.
        """
        for chunk in chunks:
            self.indexed_data.add(chunk)
        return self.indexed_data



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

