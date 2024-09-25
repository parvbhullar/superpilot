from superpilot.core.store.base import StoreBase
from superpilot.core.store.vectorstore.vespa.base import VespaStore

store = VespaStore()

store.index()