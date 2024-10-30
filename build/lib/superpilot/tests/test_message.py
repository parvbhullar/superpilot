import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.examples.persona.schema import Message


message = {
    "block": "html",
    "block_type": "question",
    "data": {
        "content": "Provide the summary of SUNIL Kumar",
        "files": [
            {
                "object_type": "post",
                "object_id": None,
                "size": 32085,
                "media_id": "bcf39212768411ef9b3266ac95333f55",
                "media_type": "txt",
                "media_relation": "attachment",
                "name": "KUMAR M CIBIL (BC EVATE).pdf",
                "media_url": "https://unpodbackend.s3.amazonaws.com/media/media/knowledge-base/evatetech.com/documents-ka8k6fy7/document/KUMAR_M_CIBIL_BC_EVATE.pdf",
                "url": "/Users/zestgeek-29/Desktop/Work/samples/sample1.txt",
                "sequence_number": 0,
            }
        ],
        "conversation_type": "initiate",
        "source": "qa2",
        "knowledge_bases": [""],
    },
    "parent_id": None,
    "pilot": "superpilot",
    "history": [
        {
            "block": "html",
            "block_type": "question",
            "data": {
                "content": "Provide the summary of SUNIL Kumar",
                "files": [
                    {
                        "object_type": "post",
                        "object_id": None,
                        "size": 32085,
                        "media_id": "bcf39212768411ef9b3266ac95333f55",
                        "media_type": "pdf",
                        "media_relation": "attachment",
                        "name": "KUMAR M CIBIL (BC EVATE).pdf",
                        "media_url": "https://unpodbackend.s3.amazonaws.com/media/media/knowledge-base/evatetech.com/documents-ka8k6fy7/document/KUMAR_M_CIBIL_BC_EVATE.pdf",
                        "url": "/Users/zestgeek-29/Desktop/Work/samples/sample2.txt",
                        "sequence_number": 0,
                    }
                ],
                "conversation_type": "initiate",
                "source": "qa2",
                "knowledge_bases": [""],
            },
            "parent_id": None,
            "pilot": "superpilot",
        }
    ],
}

msg = Message.from_block(message)
print(msg)