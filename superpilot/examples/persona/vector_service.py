import concurrent
import hashlib
import json
import os

import dspy
from typing import Callable, Union, List
import logging
import requests


class ServiceRM(dspy.Retrieve):
    def __init__(self,
                 service_url,
                 api_key=None,
                 k=30,
                 is_valid_source: Callable = None,
                 logger=logging.getLogger()
                 ):
        super().__init__(k=k)
        self.service_url = service_url
        self.logger = logger

        if not api_key and not os.environ.get("SERVICE_RM_API_KEY"):
            # raise RuntimeError(
            self.logger.warning("You must supply api_key or set environment variable SERVICE_RM_API_KEY")
            self.api_key = api_key
        else:
            self.api_key = os.environ["SERVICE_RM_API_KEY"]
        self.usage = 0

        # If not None, is_valid_source shall be a function that takes a URL and returns a boolean.
        if is_valid_source:
            self.is_valid_source = is_valid_source
        else:
            self.is_valid_source = lambda x: True



    def get_usage_and_reset(self):
        usage = self.usage
        self.usage = 0

        return {"ServiceRM": usage}

    def forward(
        self, query_or_queries: Union[str, List[str]], kn_bases:List[str] = [], exclude_urls: List[str] = []
    ):
        """Search with You.com for self.k top passages for query or queries

        Args:
            query_or_queries (Union[str, List[str]]): The query or queries to search for.
            exclude_urls (List[str]): A list of urls to exclude from the search results.

        Returns:
            a list of Dicts, each dict has keys of 'description', 'snippets' (list of strings), 'title', 'url'
        """
        queries = (
            [query_or_queries]
            if isinstance(query_or_queries, str)
            else query_or_queries
        )
        self.usage += len(queries)
        collected_results = []
        for query in queries:
            try:
                headers = {}
                if self.api_key:
                    headers["X-API-Key"] = self.api_key
                payload = {"query": query}
                if kn_bases:
                    payload["kn_token"] = kn_bases
                results = requests.post(
                    f"{self.service_url}",
                    headers=headers,
                    json=payload,
                ).json()

                authoritative_results = []
                for r in results.get("data", results.get("hits", [])):
                    if "url" not in r:
                        authoritative_results.append(r)
                    elif self.is_valid_source(r["url"]) and r["url"] not in exclude_urls:
                        authoritative_results.append(r)
                # if "hits" in results:
                collected_results.extend(authoritative_results[: self.k])
            except Exception as e:
                self.logger.error(f"Error occurs when searching query {query}: {e}")

        return collected_results


class Information:
    """Class to represent detailed information.

    Attributes:
        blurb (str): Brief blurb or summary.
        content (str): Main content of the information.
        source_type (str): Type of the source (e.g., "file", "web").
        document_id (str): Unique identifier for the document.
        semantic_identifier (str): Semantic identifier, such as a filename.
        metadata (dict): Additional metadata associated with the information.
        url (str): Unique URL or identifier for the information.
        citation_uuid (int): Citation UUID, default is -1.
    """

    def __init__(
        self,
        blurb,
        content,
        source_type,
        document_id,
        semantic_identifier,
        metadata,
        url=None,
    ):
        """Initialize the Information object with detailed attributes.

        Args:
            blurb (str): Brief blurb or summary.
            content (str): Main content of the information.
            source_type (str): Type of the source.
            document_id (str): Unique identifier for the document.
            semantic_identifier (str): Semantic identifier.
            metadata (dict): Additional metadata.
            url (str, optional): Unique URL or identifier. Defaults to document_id.
        """
        self.blurb = blurb
        self.content = content
        self.source_type = source_type
        self.document_id = document_id
        self.semantic_identifier = semantic_identifier
        self.metadata = metadata
        self.url = url if url is not None else self.document_id
        self.citation_uuid = -1

    def __eq__(self, other):
        if not isinstance(other, Information):
            return False
        return (
            self.url == other.url
            and self.blurb == other.blurb
            and self.content == other.content
            and self.source_type == other.source_type
            and self.document_id == other.document_id
            and self.semantic_identifier == other.semantic_identifier
            and self.metadata == other.metadata
        )

    def __hash__(self):
        return int(
            self._md5_hash(
                (
                    self.url,
                    self.blurb,
                    self.content,
                    self.source_type,
                    self.document_id,
                    self.semantic_identifier,
                    self._metadata_str(),
                )
            ),
            16,
        )

    def _metadata_str(self):
        """Generate a string representation of metadata."""
        return json.dumps(self.metadata, sort_keys=True)

    def _md5_hash(self, value):
        """Generate an MD5 hash for a given value."""
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value, sort_keys=True)
        return hashlib.md5(str(value).encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, info_dict):
        """Create an Information object from a dictionary.

        Args:
            info_dict (dict): Dictionary containing keys corresponding to the object's attributes.

        Returns:
            Information: An instance of Information.
        """
        return cls(
            blurb=info_dict.get("blurb", ""),
            content=info_dict.get("content", ""),
            source_type=info_dict.get("source_type", ""),
            document_id=info_dict.get("document_id", ""),
            semantic_identifier=info_dict.get("semantic_identifier", ""),
            metadata=info_dict.get("metadata", {}),
            url=info_dict.get("url"),
        )

    def to_dict(self):
        """Convert the Information object to a dictionary."""
        return {
            "blurb": self.blurb,
            "content": self.content,
            "source_type": self.source_type,
            "document_id": self.document_id,
            "semantic_identifier": self.semantic_identifier,
            "metadata": self.metadata,
            "url": self.url,
            "citation_uuid": self.citation_uuid,
        }

class QuestionToQuery(dspy.Signature):
    """You want to answer the question using Google search. What do you type in the search box?
    Write the queries you will use in the following format:
    - query 1
    - query 2
    ...
    - query n"""

    topic = dspy.InputField(prefix="Topic you are discussing about: ", format=str)
    question = dspy.InputField(prefix="Question you want to answer: ", format=str)
    queries = dspy.OutputField(format=str)

class Retriever:
    """
    An abstract base class for retriever modules. It provides a template for retrieving information based on a query.

    This class should be extended to implement specific retrieval functionalities.
    Users can design their retriever modules as needed by implementing the retrieve method.
    The retrieval model/search engine used for each part should be declared with a suffix '_rm' in the attribute name.
    """

    def __init__(self, rm: dspy.Retrieve, max_thread: int = 1):
        self.max_search_queries = 3
        self.max_thread = max_thread
        self.rm = rm

    def collect_and_reset_rm_usage(self):
        combined_usage = []
        if hasattr(getattr(self, "rm"), "get_usage_and_reset"):
            combined_usage.append(getattr(self, "rm").get_usage_and_reset())

        name_to_usage = {}
        for usage in combined_usage:
            for model_name, query_cnt in usage.items():
                if model_name not in name_to_usage:
                    name_to_usage[model_name] = query_cnt
                else:
                    name_to_usage[model_name] += query_cnt

        return name_to_usage

    def retrieve(
        self, query: Union[str, List[str]], kn_bases: List[str] = [],
            exclude_urls: List[str] = []
    ) -> List[Information]:
        queries = query if isinstance(query, list) else [query]
        to_return = []

        def process_query(q):
            retrieved_data_list = self.rm(
                query_or_queries=[q], kn_bases=kn_bases, exclude_urls=exclude_urls
            )
            local_to_return = []
            for data in retrieved_data_list:
                storm_info = Information.from_dict(data)
                storm_info.metadata["query"] = q
                local_to_return.append(storm_info)
            return local_to_return

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_thread
        ) as executor:
            results = list(executor.map(process_query, queries))

        for result in results:
            to_return.extend(result)

        return to_return

    def search(self, query: str, kn_bases: List[str] = [], exclude_urls: List[str] = []) -> str:
        queries = [query] # TODO create multiple queries if needed.
        # Search
        searched_results: List[Information] = self.retrieve(
            list(set(queries)), kn_bases=kn_bases, exclude_urls=exclude_urls
        )
        info = ""
        if len(searched_results) > 0:
            # Evaluate: Simplify this part by directly using the top 1 snippet.
            for n, r in enumerate(searched_results):
                info += f"[{n + 1}]: {r.content}"
                # info += "\n".join(f"[{n + 1}]: {k}:{v}" for k, v in r.metadata)
                info += "\n\n"
        return info

    def multiple_queries(self, query):
        # Identify: Break down question into queries.
        self.generate_queries = dspy.Predict(QuestionToQuery)
        queries = self.generate_queries(query).queries
        queries = [
            q.replace("-", "").strip().strip('"').strip('"').strip()
            for q in queries.split("\n")
        ]
        queries = queries[: self.max_search_queries]