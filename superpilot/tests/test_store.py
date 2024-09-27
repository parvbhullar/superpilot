from superpilot.core.store.base import StoreBase
from superpilot.superpilot.core.store.vectorstore.vespa.vespa_base import VespaStore
from superpilot.core.store.schema import Object, ObjectType, Privacy
from datetime import datetime
store = VespaStore()

store.index()

test_data = [
    Object(
        blurb="Test Object 1",
        content="This is the first test object.",
        source="test_source_1",
        type=ObjectType.TEXT,
        metadata={"key1": "value1"},
        ref_id="ref1",
        obj_id="obj1",
        privacy=Privacy.Public,
        embeddings={},
        timestamp=datetime.now()
    ),
    Object(
        blurb="Test Object 2",
        content="This is the second test object.",
        source="test_source_2",
        type=ObjectType.JSON,
        metadata={"key2": "value2"},
        ref_id="ref2",
        obj_id="obj2",
        privacy=Privacy.Private,
        embeddings={},
        timestamp=datetime.now()
    )
]

# Index the test data
indexed_objects = store.index(test_data)

# Output the indexed objects
for obj in indexed_objects:
    print(f"Indexed Object ID: {obj.obj_id}, Content: {obj.content}")
