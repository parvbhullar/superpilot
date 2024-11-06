from fastapi import FastAPI, HTTPException
import sys
import os
from pydantic import BaseModel
import asyncio

# Add the parent directory to the system path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.core.store.vectorstore.vespa.vespa_file_index import call_main_function
from superpilot.core.store.search.retrieval.query_escalator import *
from superpilot.core.store.search.retrieval.search_runner import query_processing
from superpilot.core.memory.vespa_memory import MemoryManager
from superpilot.core.store.vectorstore.vespa.configs.constants import DocumentSource

class Document:
    """Custom Document class to hold unstructured elements and markdown content."""
    def __init__(self, id: str, elements: list, markdown: str, **kwargs):
        self.id = id
        self.elements = elements
        self.markdown = markdown  # New attribute for markdown content
        self.source = kwargs.get('source', DocumentSource.FILE)
        self.semantic_identifier = kwargs.get('semantic_identifier')
        self.title = kwargs.get('title')
        self.doc_updated_at = kwargs.get('doc_updated_at')
        self.primary_owners = kwargs.get('primary_owners')
        self.secondary_owners = kwargs.get('secondary_owners')
        self.metadata = kwargs.get('metadata')
        self.hub_id = kwargs.get('hub_id')
        self.kn_token = kwargs.get('kn_token')

class IngestRequest(BaseModel):
    file_path: str




app = FastAPI()

@app.post("/ingest", response_model=dict)
def ingest_document(request: IngestRequest):
    file_path = request.file_path
    
    # Call your ingest function
    vespa_url='http://localhost:8081/'
    memory=MemoryManager(store_url=vespa_url,ref_id='test_memory')
    document=memory.ingest(source=file_path,ingest_type='file_path',ingest_config={},save=True)
        
    if document is None:
        raise HTTPException(status_code=500, detail="Failed to create document")

    return {
        "id": str(document.id),
        "title": str(document.title),
        "source": str(document.source.value),
        "elements": str(document.elements),
        "markdown": str(document.markdown),
        "doc_updated_at": str(document.doc_updated_at),
        "primary_owners": str(document.primary_owners),
        "secondary_owners": str(document.secondary_owners),
        "metadata": document.metadata,
        "hub_id": str(document.hub_id),
        "kn_token": str(document.kn_token)
    }

