import string
from collections.abc import Callable

import nltk  # type:ignore
from nltk.corpus import stopwords  # type:ignore
from nltk.stem import WordNetLemmatizer  # type:ignore
from nltk.tokenize import word_tokenize 
import numpy # type:ignore
from sqlalchemy.orm import Session

from typing import List, Dict, Union, Optional,Any
from superpilot.core.store.chat.chat_models import LlmDoc
from superpilot.core.store.vectorstore.vespa.configs.chat_configs import HYBRID_ALPHA
from superpilot.core.store.vectorstore.vespa.configs.chat_configs import MULTILINGUAL_QUERY_EXPANSION
# from super_store.db.embedding_model import get_current_db_embedding_model
from superpilot.core.store.document_index.interfaces import DocumentIndex
from superpilot.core.store.search.enums import EmbedTextType
from superpilot.core.store.search.models import ChunkMetric
from superpilot.core.store.search.models import IndexFilters
from superpilot.core.store.search.models import InferenceChunk
from superpilot.core.store.search.models import MAX_METRICS_CONTENT
from superpilot.core.store.search.models import RetrievalMetricsContainer
from superpilot.core.store.search.models import SearchQuery
from superpilot.core.store.search.models import SearchType
from superpilot.core.store.search.search_nlp_models import EmbeddingModel
# from super_store.secondary_llm_flows.query_expansion import multilingual_query_expansion
from superpilot.core.logging.logging import setup_logger
#from super_store.utils.threadpool_concurrency import run_functions_tuples_in_parallel
#from super_store.utils.timing import log_function_time
from superpilot.core.store.shared_configs.configs import MODEL_SERVER_HOST
from superpilot.core.store.shared_configs.configs import MODEL_SERVER_PORT

import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel
tokenizer = AutoTokenizer.from_pretrained("thenlper/gte-small")
model = AutoModel.from_pretrained("thenlper/gte-small")
get_current_db_embedding_model=model
logger = setup_logger()


def download_nltk_data() -> None:
    resources = {
        "stopwords": "corpora/stopwords",
        "wordnet": "corpora/wordnet",
        "punkt": "tokenizers/punkt",
    }

    for resource_name, resource_path in resources.items():
        try:
            nltk.data.find(resource_path)
            logger.info(f"{resource_name} is already downloaded.")
        except LookupError:
            try:
                logger.info(f"Downloading {resource_name}...")
                nltk.download(resource_name, quiet=True)
                logger.info(f"{resource_name} downloaded successfully.")
            except Exception as e:
                logger.error(f"Failed to download {resource_name}. Error: {e}")


def lemmatize_text(text: str) -> list[str]:
    try:
        lemmatizer = WordNetLemmatizer()
        word_tokens = word_tokenize(text)
        return [lemmatizer.lemmatize(word) for word in word_tokens]
    except Exception:
        return text.split(" ")


def remove_stop_words_and_punctuation(text: str) -> list[str]:
    try:
        stop_words = set(stopwords.words("english"))
        word_tokens = word_tokenize(text)
        text_trimmed = [
            word
            for word in word_tokens
            if (word.casefold() not in stop_words and word not in string.punctuation)
        ]
        return text_trimmed or word_tokens
    except Exception:
        return text.split(" ")


def query_processing(
    query: str,
) -> str:
    query = " ".join(remove_stop_words_and_punctuation(query))
    query = " ".join(lemmatize_text(query))
    return query


def combine_retrieval_results(
    chunk_sets: list[list[InferenceChunk]],
) -> list[InferenceChunk]:
    all_chunks = [chunk for chunk_set in chunk_sets for chunk in chunk_set]

    unique_chunks: dict[tuple[str, int], InferenceChunk] = {}
    for chunk in all_chunks:
        key = (chunk.document_id, chunk.chunk_id)
        if key not in unique_chunks:
            unique_chunks[key] = chunk
            continue

        stored_chunk_score = unique_chunks[key].score or 0
        this_chunk_score = chunk.score or 0
        if stored_chunk_score < this_chunk_score:
            unique_chunks[key] = chunk

    sorted_chunks = sorted(
        unique_chunks.values(), key=lambda x: x.score or 0, reverse=True
    )

    return sorted_chunks


#@log_function_time(print_only=True)
def doc_index_retrieval(
    query: SearchQuery,
    document_index: DocumentIndex,
    db_session: Session,
    hybrid_alpha: float = HYBRID_ALPHA,
) -> list[InferenceChunk]:
    if query.search_type == SearchType.KEYWORD:
        top_chunks = document_index.keyword_retrieval(
            query=query.query,
            filters=query.filters,
            time_decay_multiplier=query.recency_bias_multiplier,
            num_to_retrieve=query.num_hits,
        )
    else:
        db_embedding_model = get_current_db_embedding_model(db_session)

        model = EmbeddingModel(
            model_name=db_embedding_model.model_name,
            query_prefix=db_embedding_model.query_prefix,
            passage_prefix=db_embedding_model.passage_prefix,
            normalize=db_embedding_model.normalize,
            # The below are globally set, this flow always uses the indexing one
            server_host=MODEL_SERVER_HOST,
            server_port=MODEL_SERVER_PORT,
        )

        query_embedding = model.encode([query.query], text_type=EmbedTextType.QUERY)[0]

        if query.search_type == SearchType.SEMANTIC:
            top_chunks = document_index.semantic_retrieval(
                query=query.query,
                query_embedding=query_embedding,
                filters=query.filters,
                time_decay_multiplier=query.recency_bias_multiplier,
                num_to_retrieve=query.num_hits,
            )

        elif query.search_type == SearchType.HYBRID:
            top_chunks = document_index.hybrid_retrieval(
                query=query.query,
                query_embedding=query_embedding,
                filters=query.filters,
                time_decay_multiplier=query.recency_bias_multiplier,
                num_to_retrieve=query.num_hits,
                offset=query.offset,
                hybrid_alpha=hybrid_alpha,
            )

        else:
            raise RuntimeError("Invalid Search Flow")

    return top_chunks


def _simplify_text(text: str) -> str:
    return "".join(
        char for char in text if char not in string.punctuation and not char.isspace()
    ).lower()


def retrieve_chunks(
    query: SearchQuery,
    document_index: DocumentIndex,
    db_session: Session,
    hybrid_alpha: float = HYBRID_ALPHA,  # Only applicable to hybrid search
    multilingual_expansion_str: str | None = MULTILINGUAL_QUERY_EXPANSION,
    #multilingual_expansion_str: str | None = MULTILINGUAL_QUERY_EXPANSION,
    retrieval_metrics_callback: Callable[[RetrievalMetricsContainer], None]
    | None = None,
) -> list[InferenceChunk]:
    """Returns a list of the best chunks from an initial keyword/semantic/ hybrid search."""
    # Don't do query expansion on complex queries, rephrasings likely would not work well
    if not multilingual_expansion_str or "\n" in query.query or "\r" in query.query:
        top_chunks = doc_index_retrieval(
            query=query,
            document_index=document_index,
            db_session=db_session,
            hybrid_alpha=hybrid_alpha,
        )
    else:
        simplified_queries = set()
        run_queries: list[tuple[Callable, tuple]] = []

        # Currently only uses query expansion on multilingual use cases
        query_rephrases = multilingual_query_expansion(
            query.query, multilingual_expansion_str
        )
        # Just to be extra sure, add the original query.
        query_rephrases.append(query.query)
        for rephrase in set(query_rephrases):
            # Sometimes the model rephrases the query in the same language with minor changes
            # Avoid doing an extra search with the minor changes as this biases the results
            simplified_rephrase = _simplify_text(rephrase)
            if simplified_rephrase in simplified_queries:
                continue
            simplified_queries.add(simplified_rephrase)

            q_copy = query.copy(update={"query": rephrase}, deep=True)
            run_queries.append(
                (
                    doc_index_retrieval,
                    (q_copy, document_index, db_session, hybrid_alpha),
                )
            )
        parallel_search_results = run_functions_tuples_in_parallel(run_queries)
        top_chunks = combine_retrieval_results(parallel_search_results)

    if not top_chunks:
        logger.info(
            f"{query.search_type.value.capitalize()} search returned no results "
            f"with filters: {query.filters}"
        )
        return []

    if retrieval_metrics_callback is not None:
        chunk_metrics = [
            ChunkMetric(
                document_id=chunk.document_id,
                chunk_content_start=chunk.content[:MAX_METRICS_CONTENT],
                first_link=chunk.source_links[0] if chunk.source_links else None,
                score=chunk.score if chunk.score is not None else 0,
            )
            for chunk in top_chunks
        ]
        retrieval_metrics_callback(
            RetrievalMetricsContainer(
                search_type=query.search_type, metrics=chunk_metrics
            )
        )

    return top_chunks


#Additions 

from superpilot.core.store.schema import Object
#@log_function_time(print_only=True)
from typing import List
from transformers import pipeline
from datetime import datetime

# Assuming Object class is already defined as per your provided code

import numpy as np
from typing import List
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline
from sentence_transformers import SentenceTransformer

# Initialize a model for creating embeddings (Sentence-BERT or similar)
model = SentenceTransformer('all-MiniLM-L6-v2')  # Example, you can use others like 'paraphrase-MiniLM-L6-v2'




def retrieve_related_objects(objects: List[Object], query: str, top_n: int = 5) -> List[Object]:
    """
    Retrieves the top N objects related to the query based on content similarity.

    Args:
        objects (List[Object]): List of Object instances to search through.
        query (str): The query string to search for relevant content.
        top_n (int): Number of top relevant objects to return.

    Returns:
        List[Object]: The most relevant objects related to the query.
    """
    
    # Step 1: Embed the query using the NLP model
    query_embedding = model.encode(query)

    # Step 2: Embed all objects' content using the same model
    object_embeddings = [model.encode(obj.content) for obj in objects]

    # Step 3: Compute cosine similarities between the query and each object's content
    similarities = cosine_similarity([query_embedding], object_embeddings)[0]

    # Step 4: Get indices of the top N most similar objects
    top_indices = np.argsort(similarities)[-top_n:][::-1]

    # Step 5: Retrieve the top N most similar objects based on the computed similarities
    top_objects = [objects[i] for i in top_indices]

    return top_objects






# Example usage
# objects = [list of Object instances]
# query = "PDF file size optimization"
# top_related_objects = retrieve_related_objects(objects, query, top_n=3)


















def combine_inference_chunks(inf_chunks: list[InferenceChunk]) -> LlmDoc:
    if not inf_chunks:
        raise ValueError("Cannot combine empty list of chunks")

    # Use the first link of the document
    first_chunk = inf_chunks[0]
    chunk_texts = [chunk.content for chunk in inf_chunks]
    return LlmDoc(
        document_id=first_chunk.document_id,
        content="\n".join(chunk_texts),
        blurb=first_chunk.blurb,
        semantic_identifier=first_chunk.semantic_identifier,
        source_type=first_chunk.source_type,
        metadata=first_chunk.metadata,
        updated_at=first_chunk.updated_at,
        link=first_chunk.source_links[0] if first_chunk.source_links else None,
        source_links=first_chunk.source_links,
    )


def inference_documents_from_ids(
    doc_identifiers: list[tuple[str, int]],
    document_index: DocumentIndex,
) -> list[LlmDoc]:
    # Currently only fetches whole docs
    doc_ids_set = set(doc_id for doc_id, chunk_id in doc_identifiers)

    # No need for ACL here because the doc ids were validated beforehand
    filters = IndexFilters(access_control_list=None)

    functions_with_args: list[tuple[Callable, tuple]] = [
        (document_index.id_based_retrieval, (doc_id, None, None, filters))
        for doc_id in doc_ids_set
    ]

    parallel_results = run_functions_tuples_in_parallel(
        functions_with_args, allow_failures=True
    )

    # Any failures to retrieve would give a None, drop the Nones and empty lists
    inference_chunks_sets = [res for res in parallel_results if res]

    return [combine_inference_chunks(chunk_set) for chunk_set in inference_chunks_sets]
