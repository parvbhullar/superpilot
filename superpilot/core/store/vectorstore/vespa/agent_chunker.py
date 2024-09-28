import json
from functools import partial
from typing import List, Dict, Callable
from pydantic import BaseModel, Field
from typing import List, Dict
from collections.abc import Callable

# from llama_index import text_splitter
from transformers import AutoTokenizer
# from super_store.search.search_nlp_models import get_default_tokenizer
from superpilot.core.logging.logging import setup_logger
import requests

from superpilot.core.store.vectorstore.vespa.configs.app_configs import CHUNK_OVERLAP

# Set up logger
logger = setup_logger()
from superpilot.examples.persona.executor import AIPersona


class AIAgentChunker:
    def __init__(self, embedding_model, vespa_client):
        self.embedding_model = embedding_model
        self.vespa_client = vespa_client
        # self.tokenizer = get_default_tokenizer()

    def chunk_text(self, text: str, chunk_size: int, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """Chunks large text using a SentenceSplitter based on the chunk size."""
        splitter = text_splitter.SentenceSplitter(tokenizer=self.tokenizer.tokenize, chunk_size=chunk_size,
                                                  chunk_overlap=overlap)
        return splitter.split_text(text)

    def embed_chunks(self, chunks: List[str]) -> List[Dict]:
        """Generates embeddings for the given chunks."""
        embeddings = self.embedding_model.encode(chunks)
        return embeddings
    #
    # def process_and_chunk_persona(self, persona: Dict) -> List[DocAwareChunk]:
    #     """
    #     Takes an AIPersona model and processes it into chunks with embeddings.
    #     Chunks fields like about, persona, and questions.
    #     """
    #     chunks = []
    #
    #     # Chunk the 'about' field
    #     if persona.get('about'):
    #         about_chunks = self.chunk_text(persona['about'], DOC_EMBEDDING_CONTEXT_SIZE)
    #         about_embeddings = self.embed_chunks(about_chunks)
    #         chunks.extend(self.create_doc_chunks(about_chunks, about_embeddings, "about"))
    #
    #     # Chunk the 'persona' field
    #     if persona.get('persona'):
    #         persona_chunks = self.chunk_text(persona['persona'], DOC_EMBEDDING_CONTEXT_SIZE)
    #         persona_embeddings = self.embed_chunks(persona_chunks)
    #         chunks.extend(self.create_doc_chunks(persona_chunks, persona_embeddings, "persona"))
    #
    #     # Chunk the 'questions' field
    #     if persona.get('questions'):
    #         questions_text = " ".join(persona['questions'])
    #         questions_chunks = self.chunk_text(questions_text, DOC_EMBEDDING_CONTEXT_SIZE)
    #         questions_embeddings = self.embed_chunks(questions_chunks)
    #         chunks.extend(self.create_doc_chunks(questions_chunks, questions_embeddings, "questions"))
    #
    #     return chunks
    #
    # def create_doc_chunks(self, chunk_texts: List[str], chunk_embeddings: List[Dict], field_name: str) -> List[
    #     DocAwareChunk]:
    #     """Creates document chunks for Vespa from the chunked text and embeddings."""
    #     doc_chunks = []
    #     for i, (text, embedding) in enumerate(zip(chunk_texts, chunk_embeddings)):
    #         doc_chunk = DocAwareChunk(
    #             chunk_id=i,
    #             content=text,
    #             embeddings=embedding,
    #             field_name=field_name
    #         )
    #         doc_chunks.append(doc_chunk)
    #     return doc_chunks
    #
    # def push_to_vespa(self, chunks: List[DocAwareChunk], document_id: str):
    #     """Pushes the document chunks to Vespa server."""
    #     documents = [{"id": document_id, "fields": chunk.dict()} for chunk in chunks]
    #     for doc in documents:
    #         self.vespa_client.feed_document(doc)
    #     logger.info(f"Successfully pushed {len(documents)} chunks to Vespa for document {document_id}")
    #
    # def process_and_index_persona(self, persona: Dict, document_id: str):
    #     """Main method to chunk and index an AI persona to Vespa."""
    #     chunks = self.process_and_chunk_persona(persona)
    #     self.push_to_vespa(chunks, document_id)
    #
    #
    # def chunk(self, document: Document) -> List[DocAwareChunk]:
    #     ai_persona = AIPersona(**document.metadata)
    #
    #     chunks = []
    #     chunk_id = 0
    #
    #     # Create a chunk for the main content
    #     main_content = f"{ai_persona.persona_name}\n{ai_persona.about}\n{ai_persona.persona}"
    #     chunks.append(DocAwareChunk(
    #         source_document=document,
    #         chunk_id=chunk_id,
    #         blurb=ai_persona.about[:100],  # Use first 100 characters of about as blurb
    #         content=main_content,
    #         source_links=None,
    #         section_continuation=False
    #     ))
    #     chunk_id += 1
    #
    #     # Create chunks for questions
    #     for question in ai_persona.questions:
    #         chunks.append(DocAwareChunk(
    #             source_document=document,
    #             chunk_id=chunk_id,
    #             blurb=question[:100],
    #             content=question,
    #             source_links=None,
    #             section_continuation=False
    #         ))
    #         chunk_id += 1
    #
    #     return chunks

    def index_jsonl_to_vespa(self, jsonl_file):
        # Vespa endpoint (adjust for your Vespa instance)
        VESPA_URL = "http://localhost:8081/document/v1/agent_doc/agent_doc/docid/"
        with open(jsonl_file, 'r') as file:
            for line in file:
                record = json.loads(line)
                doc_id = record.get('handle')  # Using 'handle' as document ID
                if not doc_id:
                    continue  # Ensure document has a unique 'handle'

                # Flatten knowledge_bases (if present)
                knowledge_bases = [kb.get('name') for kb in record.get('knowledge_bases', [])]
                knowledge_base_fields = [kb.get('datasource') for kb in record.get('knowledge_bases', [])]

                # Prepare the Vespa document structure
                vespa_doc = {
                    "fields": {
                        "persona_name": record.get("persona_name", ""),
                        "handle": record.get("handle", ""),
                        "about": record.get("about", ""),
                        "persona": record.get("persona", ""),
                        "tags": record.get("tags", []),
                        "questions": record.get("questions", []),
                        "knowledge_bases": knowledge_bases,
                        "knowledge_base_fields": knowledge_base_fields,
                        # Optional embeddings if provided in the data
                        "persona_embedding": record.get("persona_embedding", []),
                        "questions_embedding": record.get("questions_embedding", [])
                    }
                }

                # Index the document to Vespa
                response = requests.post(VESPA_URL + doc_id, json=vespa_doc)

                # Handle response
                if response.status_code == 200:
                    print(f"Indexed document {doc_id} successfully")
                else:
                    print(f"Failed to index document {doc_id}: {response.text}")





# def index_ai_persona_batch(
#         *,
#         chunker: AIPersonaChunker,
#         embedder: IndexingEmbedder,
#         document_index: DocumentIndex,
#         documents: List[Document],
#         index_attempt_metadata: IndexAttemptMetadata,
#         db_session: Session,
# ) -> tuple[int, int]:
#     logger.debug("Starting AI Persona chunking")
#     chunks: List[DocAwareChunk] = []
#     for document in documents:
#         chunks.extend(chunker.chunk(document))
#
#     logger.debug("Starting embedding")
#     chunks_with_embeddings = embedder.embed_chunks(chunks=chunks)
#
#     logger.debug(f"Indexing the following chunks: {[chunk.to_short_descriptor() for chunk in chunks]}")
#
#     # Prepare the Vespa document
#     vespa_docs = []
#     for chunk in chunks_with_embeddings:
#         ai_persona = AIPersona(**chunk.source_document.metadata)
#         vespa_doc = {
#             "persona_name": ai_persona.persona_name,
#             "handle": ai_persona.handle,
#             "about": ai_persona.about,
#             "persona": ai_persona.persona,
#             "tags": ai_persona.tags,
#             "questions": ai_persona.questions,
#             "knowledge_bases": ai_persona.knowledge_bases,
#             "knowledge_base_fields": ai_persona.knowledge_base_fields,
#             "persona_embedding": chunk.embeddings.full_embedding,
#             "questions_embedding": chunk.embeddings.mini_chunk_embeddings[
#                 0] if chunk.embeddings.mini_chunk_embeddings else None,
#             "embeddings": {
#                 "0": chunk.embeddings.full_embedding,
#                 **{str(i + 1): emb for i, emb in enumerate(chunk.embeddings.mini_chunk_embeddings)}
#             },
#             "boost": 1.0,  # Default boost value
#             "hidden": False,
#             "doc_updated_at": int(
#                 chunk.source_document.doc_updated_at.timestamp()) if chunk.source_document.doc_updated_at else None,
#             "owners": chunk.source_document.primary_owners
#         }
#         vespa_docs.append(vespa_doc)
#
#     # Push documents to Vespa
#     insertion_records = document_index.index(chunks=vespa_docs)
#
#     return len([r for r in insertion_records if r.already_existed is False]), len(chunks)
#
#
# def build_ai_persona_indexing_pipeline(
#         *,
#         embedder: IndexingEmbedder,
#         document_index: DocumentIndex,
#         db_session: Session,
# ) -> Callable:
#     chunker = AIPersonaChunker()
#
#     return partial(
#         index_ai_persona_batch,
#         chunker=chunker,
#         embedder=embedder,
#         document_index=document_index,
#         db_session=db_session,
#     )