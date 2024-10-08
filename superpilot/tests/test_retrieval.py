#from superpilot.core.store.search.search_token import get_document_search
import sys
import os
import string
import nltk

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from sqlalchemy.orm import Session



sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.core.store.search.retrieval.search_runner import retrieve_related_objects
from superpilot.core.store.search.retrieval.search_runner import query_processing
#from superpilot.core.store.search.retrieval.search_runner import retrieve_related_objects
from superpilot.core.store.search.models import SearchQuery
from superpilot.core.store.base import DocumentIndexer
from superpilot.core.store.search.models import IndexFilters

index_filter =IndexFilters(access_control_list=[])


from superpilot.core.memory.vespa_memory import MemoryManager
vespa_url='http://localhost:8081/document/v1/'
memory=MemoryManager(store_url=vespa_url,ref_id='test_memory')
chunks=memory.get_all_memory()

#from vespa.application import Vespa
c=1
print('All chunks:')
for chunk in chunks:
    print(c,chunk.obj_id)
    c=c+1
    print()

query_string=input('Enter Query:')
query_string=query_processing(query_string)

filter={
    'blurb':'Artifial Intelligence'
}
#session=Session()
top_chunks=retrieve_related_objects(query=query_string,objects=chunks)
#top_chunks=search(query=query_string,objects=chunks,filter=filter)

for chunks in top_chunks:
    print(chunks.obj_id)







