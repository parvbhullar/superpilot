import sys
import os

# Add the correct path to the 'superpilot' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from superpilot.core.store.vectorstore.vespa.vespa_base import VespaStore

vespa_store = VespaStore(index_name="unpod_chunk", secondary_index_name="unpod_chunk_search")
vespa_store.create_index()
