from abc import ABC, abstractmethod
from typing import Any,List,Set

from superpilot.core.store.schema import InferenceObject, Object


class Verifiable(ABC):
    """
    Class must implement document index schema verification. For example, verify that all of the
    necessary attributes for indexing, querying, filtering, and fields to return from search are
    all valid in the schema.

    Parameters:
    - index_name: The name of the primary index currently used for querying
    - secondary_index_name: The name of the secondary index being built in the background, if it
            currently exists. Some functions on the document index act on both the primary and
            secondary index, some act on just one.
    """

    @abstractmethod
    def __init__(
        self,
        index_name: str,
        secondary_index_name: str | None,
        *args: Any,
        **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.index_name = index_name
        self.secondary_index_name = secondary_index_name

    @abstractmethod
    def ensure_indices_exist(
        self,
        index_embedding_dim: int,
        secondary_index_embedding_dim: int | None,
    ) -> None:
        """
        Verify that the document index exists and is consistent with the expectations in the code.

        Parameters:
        - index_embedding_dim: Vector dimensionality for the vector similarity part of the search
        - secondary_index_embedding_dim: Vector dimensionality of the secondary index being built
                behind the scenes. The secondary index should only be built when switching
                embedding models therefore this dim should be different from the primary index.
        """
        raise NotImplementedError


class DocumentIndexer(Indexable):
    def index(self, chunks: List[Object]) -> Set[str]:
        """
        Indexes the provided chunks, overwriting existing chunks if necessary.
        """
        document_ids = set()

        for chunk in chunks:
            # Ensure the document gets reindexed (clear existing first)
            if chunk.obj_id in self.primary_index:
                del self.primary_index[chunk.obj_id]  # Clear existing entry

            # Index the new chunk
            self.primary_index[chunk.obj_id] = chunk

            # Add document ID to the set
            document_ids.add(chunk.obj_id)

        return document_ids

class Indexable(ABC):
    """
    Class must implement the ability to index document chunks
    """

    def __init__(self):
        self.primary_index={}


    @abstractmethod
    def index(
        self,
        chunks: list[Object],
    ) -> set[Object]:
        

        """
        Takes a list of document chunks and indexes them in the document index

        NOTE: When a document is reindexed/updated here, it must clear all of the existing document
        chunks before reindexing. This is because the document may have gotten shorter since the
        last run. Therefore, upserting the first 0 through n chunks may leave some old chunks that
        have not been written over.

        NOTE: The chunks of a document are never separated into separate index() calls. So there is
        no worry of receiving the first 0 through n chunks in one index call and the next n through
        m chunks of a docu in the next index call.

        NOTE: Due to some asymmetry between the primary and secondary indexing logic, this function
        only needs to index chunks into the PRIMARY index. Do not update the secondary index here,
        it is done automatically outside of this code.

        Parameters:
        - chunks: Document chunks with all of the information needed for indexing to the document
                index.

        Returns:
            List of document ids which map to unique documents and are used for deduping chunks
            when updating, as well as if the document is newly indexed or already existed and
            just updated
        """
        raise NotImplementedError


class Deletable(ABC):
    """
    Class must implement the ability to delete document by their unique document ids.
    """

    @abstractmethod
    def delete(self, doc_ids: list[str]) -> None:
        """
        Given a list of document ids, hard delete them from the document index

        Parameters:
        - doc_ids: list of document ids as specified by the connector
        """
        raise NotImplementedError


class Updatable(ABC):
    """
    Class must implement the ability to update certain attributes of a document without needing to
    update all of the fields. Specifically, needs to be able to update:
    - Access Control List
    - Document-set membership
    - Boost value (learning from feedback mechanism)
    - Whether the document is hidden or not, hidden documents are not returned from search
    """

    @abstractmethod
    def update(self, update_requests: list[Object]) -> None:
        """
        Updates some set of chunks. The document and fields to update are specified in the update
        requests. Each update request in the list applies its changes to a list of document ids.
        None values mean that the field does not need an update.

        Parameters:
        - update_requests: for a list of document ids in the update request, apply the same updates
                to all of the documents with those ids. This is for bulk handling efficiency. Many
                updates are done at the connector level which have many documents for the connector
        """
        raise NotImplementedError


class IdRetrievalCapable(ABC):
    """
    Class must implement the ability to retrieve either:
    - all of the chunks of a document IN ORDER given a document id.
    - a specific chunk given a document id and a chunk index (0 based)
    """

    @abstractmethod
    def id_based_retrieval(
        self,
        ref_id: str,
        min_chunk_ind: int | None,
        max_chunk_ind: int | None,
        user_access_control_list: list[str] | None = None,
    ) -> list[InferenceObject]:
        """
        Fetch chunk(s) based on document id

        NOTE: This is used to reconstruct a full document or an extended (multi-chunk) section
        of a document. Downstream currently assumes that the chunking does not introduce overlaps
        between the chunks. If there are overlaps for the chunks, then the reconstructed document
        or extended section will have duplicate segments.

        Parameters:
        - ref_id: document id for which to retrieve the chunk(s)
        - min_chunk_ind: if None then fetch from the start of doc
        - max_chunk_ind:
        - filters: standard filters object, in this case only the access filter is applied as a
                permission check

        Returns:
            list of chunks for the document id or the specific chunk by the specified chunk index
            and document id
        """
        raise NotImplementedError


class KeywordCapable(ABC):
    """
    Class must implement the keyword search functionality
    """

    @abstractmethod
    def keyword_retrieval(
        self,
        query: str,
        filters: Any, # IndexFilters,
        time_decay_multiplier: float,
        num_to_retrieve: int,
        offset: int = 0,
    ) -> list[InferenceObject]:
        """
        Run keyword search and return a list of chunks. Inference chunks are chunks with all of the
        information required for query time purposes. For example, some details of the document
        required at indexing time are no longer needed past this point. At the same time, the
        matching keywords need to be highlighted.

        NOTE: the query passed in here is the unprocessed plain text query. Preprocessing is
        expected to be handled by this function as it may depend on the index implementation.
        Things like query expansion, synonym injection, stop word removal, lemmatization, etc. are
        done here.

        Parameters:
        - query: unmodified user query
        - filters: standard filter object
        - time_decay_multiplier: how much to decay the document scores as they age. Some queries
                based on the persona settings, will have this be a 2x or 3x of the default
        - num_to_retrieve: number of highest matching chunks to return
        - offset: number of highest matching chunks to skip (kind of like pagination)

        Returns:
            best matching chunks based on keyword matching (should be BM25 algorithm ideally)
        """
        raise NotImplementedError


class VectorCapable(ABC):
    """
    Class must implement the vector/semantic search functionality
    """

    @abstractmethod
    def semantic_retrieval(
        self,
        query: str,  # Needed for matching purposes
        query_embedding: list[float],
        filters: Any, # IndexFilters,
        time_decay_multiplier: float,
        num_to_retrieve: int,
        offset: int = 0,
    ) -> list[InferenceObject]:
        """
        Run vector/semantic search and return a list of inference chunks.

        Parameters:
        - query: unmodified user query. This is needed for getting the matching highlighted
                keywords
        - query_embedding: vector representation of the query, must be of the correct
                dimensionality for the primary index
        - filters: standard filter object
        - time_decay_multiplier: how much to decay the document scores as they age. Some queries
                based on the persona settings, will have this be a 2x or 3x of the default
        - num_to_retrieve: number of highest matching chunks to return
        - offset: number of highest matching chunks to skip (kind of like pagination)

        Returns:
            best matching chunks based on vector similarity
        """
        raise NotImplementedError


class HybridCapable(ABC):
    """
    Class must implement hybrid (keyword + vector) search functionality
    """

    @abstractmethod
    def hybrid_retrieval(
        self,
        query: str,
        query_embedding: list[float],
        filters: Any, #IndexFilters,
        time_decay_multiplier: float,
        num_to_retrieve: int,
        offset: int = 0,
        hybrid_alpha: float | None = None,
    ) -> list[InferenceObject]:
        """
        Run hybrid search and return a list of inference chunks.

        NOTE: the query passed in here is the unprocessed plain text query. Preprocessing is
        expected to be handled by this function as it may depend on the index implementation.
        Things like query expansion, synonym injection, stop word removal, lemmatization, etc. are
        done here.

        Parameters:
        - query: unmodified user query. This is needed for getting the matching highlighted
                keywords
        - query_embedding: vector representation of the query, must be of the correct
                dimensionality for the primary index
        - filters: standard filter object
        - time_decay_multiplier: how much to decay the document scores as they age. Some queries
                based on the persona settings, will have this be a 2x or 3x of the default
        - num_to_retrieve: number of highest matching chunks to return
        - offset: number of highest matching chunks to skip (kind of like pagination)
        - hybrid_alpha: weighting between the keyword and vector search results. It is important
                that the two scores are normalized to the same range so that a meaningful
                comparison can be made. 1 for 100% weighting on vector score, 0 for 100% weighting
                on keyword score.

        Returns:
            best matching chunks based on weighted sum of keyword and vector/semantic search scores
        """
        raise NotImplementedError


class AdminCapable(ABC):
    """
    Class must implement a search for the admin "Explorer" page. The assumption here is that the
    admin is not "searching" for knowledge but has some document already in mind. They are either
    looking to positively boost it because they know it's a good reference document, looking to
    negatively boost it as a way of "deprecating", or hiding the document.

    Assuming the admin knows the document name, this search has high emphasis on the title match.

    Suggested implementation:
    Keyword only, BM25 search with 5x weighting on the title field compared to the contents
    """

    @abstractmethod
    def admin_retrieval(
        self,
        query: str,
        filters: Any, #IndexFilters,
        num_to_retrieve: int,
        offset: int = 0,
    ) -> list[InferenceObject]:
        """
        Run the special search for the admin document explorer page

        Parameters:
        - query: unmodified user query. Though in this flow probably unmodified is best
        - filters: standard filter object
        - num_to_retrieve: number of highest matching chunks to return
        - offset: number of highest matching chunks to skip (kind of like pagination)

        Returns:
            list of best matching chunks for the explorer page query
        """
        raise NotImplementedError
