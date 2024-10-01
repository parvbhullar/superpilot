
from superpilot.core.store.schema import Object

import requests
from typing import List, Union


#vespa_url="http://localhost:8080/document/v1/<namespace>/<document-type>/"
class MemoryManager:
    def __init__(self, vespa_url: str, ref_id: str):
        self.vespa_url = vespa_url
        self.ref_id = ref_id

    
    def convert_to_objects(self,input_data: Union[str, dict]):
        pass

    

    def add_memory(self, input_data: Union[str, dict], ref_id: str):
        """Add memory to Vespa AI engine."""
        objects = self.convert_to_objects(input_data)
        for obj in objects:
            response = requests.post(f"{self.vespa_url}/docid/{ref_id}", json=obj.dict())
            if response.status_code != 200:
                print(f"Error adding memory: {response.text}")

    def get_all_memories(self) -> List[Object]:
        """Retrieve all memories from Vespa AI engine."""
        response = requests.get(f"{self.vespa_url}/docid/{self.ref_id}")
        if response.status_code == 200:
            return [Object(**item) for item in response.json()]
        else:
            print(f"Error retrieving memories: {response.text}")
            return []

    def get_memory(self, query: str) -> Union[Object, None]:
        """Retrieve a specific object by querying its blurb."""
        all_memories = self.get_all_memories()
        for memory in all_memories:
            if query.lower() in memory.blurb.lower():
                return memory
        return None
    
    