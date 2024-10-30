import re
from collections.abc import Iterator
from typing import List, Dict, Optional, Union

# from superpilot.core.store.chat.chat_models import AnswerQuestionStreamReturn
# from superpilot.core.store.chat.chat_models import CitationInfo
# from superpilot.core.store.chat.chat_models import UnpodAnswerPiece
from superpilot.core.store.vectorstore.vespa.configs.constants import DocumentSource
from superpilot.core.store.chat.chat_models import LlmDoc
from superpilot.core.store.vectorstore.vespa.configs.chat_configs import STOP_STREAM_PAT
# from superpilot.examples.answering.models import StreamProcessor
#from superpilot.examples.answering.stream_processing.utils import map_document_id_order
from superpilot.core.logging.logging import setup_logger
from pydantic import BaseModel

TRIPLE_BACKTICK = "```"
logger = setup_logger()

def in_code_block(llm_text: str) -> bool:
    count = llm_text.count(TRIPLE_BACKTICK)
    return count % 2 != 0

def convert_docs_to_llmdoc(doc_list: List[Dict[str, Union[str, dict]]]) -> List[LlmDoc]:
    """
    Converts a list of dictionaries into a list of LlmDoc instances.
    """
    llm_docs = []
    for doc in doc_list:
        try:
            llm_doc = LlmDoc(
                document_id=doc["document_id"],
                content=doc["content"],
                blurb=doc["blurb"],
                semantic_identifier=doc["semantic_identifier"],
                source_type=DocumentSource(doc["source_type"]),
                metadata=doc["metadata"],
                updated_at=None,
                link=doc.get("link"),
                source_links=doc.get("source_links")
            )
            llm_docs.append(llm_doc)
        except KeyError as e:
            logger.error(f"Missing key in document: {e}")
    return llm_docs

class Citation(BaseModel):
    """
    A class to represent citations from a list of LlmDoc instances.
    """
    document_ids: List[str]
    blurbs: List[str]
    source_types: List[str]
    links: List[Optional[str]]
    source_links: List[Optional[Dict[int, str]]]
    citation_num: Optional[int] = None  # New attribute to track citation numbers
    extracted_id: Optional[str] = None  # Attribute to track id coming from `extract_citations_from_stream`

    @classmethod
    def from_llm_docs(cls, llm_docs: List[LlmDoc], extracted_id: str = None) -> "Citation":
        """
        Convert a list of LlmDoc instances to a Citation instance, including extracted citation id.
        """
        document_ids = [doc.document_id for doc in llm_docs]
        blurbs = [doc.blurb for doc in llm_docs]
        source_types = [doc.source_type.value for doc in llm_docs]
        links = [doc.link for doc in llm_docs]
        source_links = [doc.source_links for doc in llm_docs]

        return cls(
            document_ids=document_ids,
            blurbs=blurbs,
            source_types=source_types,
            links=links,
            source_links=source_links,
            extracted_id=extracted_id
        )

def extract_citations_from_stream(
    tokens: Iterator[str],
    context_docs: List[LlmDoc],
    doc_id_to_rank_map: Dict[str, int],
    stop_stream: Optional[str] = STOP_STREAM_PAT,
) -> Iterator[Union[UnpodAnswerPiece, CitationInfo]]:
    """
    Extract citations from the token stream.
    """
    llm_out = ""
    max_citation_num = len(context_docs)
    curr_segment = ""
    prepend_bracket = False
    cited_inds = set()
    hold = ""
    
    for raw_token in tokens:
        if stop_stream:
            next_hold = hold + raw_token

            if stop_stream in next_hold:
                break

            if next_hold == stop_stream[: len(next_hold)]:
                hold = next_hold
                continue

            token = next_hold
            hold = ""
        else:
            token = raw_token

        curr_segment += token
        llm_out += token

        possible_citation_pattern = r"(\[\d*$)"
        citation_pattern = r"\[(\d+)\]"
        citation_found = re.search(citation_pattern, curr_segment)

        if citation_found and not in_code_block(llm_out):
            numerical_value = int(citation_found.group(1))
            if 1 <= numerical_value <= max_citation_num:
                context_llm_doc = context_docs[numerical_value - 1]

                link = context_llm_doc.link
                target_citation_num = doc_id_to_rank_map[context_llm_doc.document_id]

                curr_segment = re.sub(
                    rf"\[{numerical_value}\]", f"[{target_citation_num}]", curr_segment
                )

                if target_citation_num not in cited_inds:
                    cited_inds.add(target_citation_num)
                    yield CitationInfo(
                        citation_num=target_citation_num,
                        document_id=context_llm_doc.document_id,
                    )

                if link:
                    curr_segment = re.sub(r"\[", "[[", curr_segment, count=1)
                    curr_segment = re.sub("]", f"]]({link})", curr_segment, count=1)

        if re.search(possible_citation_pattern, curr_segment):
            continue

        if curr_segment and curr_segment[-1] == "[":
            curr_segment = curr_segment[:-1]
            prepend_bracket = True

        yield UnpodAnswerPiece(answer_piece=curr_segment)
        curr_segment = ""

    if curr_segment:
        if prepend_bracket:
            yield UnpodAnswerPiece(answer_piece="[" + curr_segment)
        else:
            yield UnpodAnswerPiece(answer_piece=curr_segment)

def build_citation_processor(
    context_docs: List[LlmDoc], search_order_docs: List[LlmDoc]
) -> StreamProcessor:
    """
    Build a citation processor to handle token streams.
    """
    def stream_processor(tokens: Iterator[str]) -> AnswerQuestionStreamReturn:
        yield from extract_citations_from_stream(
            tokens=tokens,
            context_docs=context_docs,
            doc_id_to_rank_map=map_document_id_order(search_order_docs),
        )

    return stream_processor

def get_citation(docs: List[Dict[str, Union[str, dict]]], msg: str) -> Citation:
    """
    Extract citations from a list of document dictionaries and the message stream.
    """
    tokens = iter(msg.split(' '))
    llm_docs = convert_docs_to_llmdoc(docs)
    
    # Simulating document ID map for ranks based on docs
    doc_id_to_rank_map = {doc.document_id: idx + 1 for idx, doc in enumerate(llm_docs)}
    
    citation_info = None
    # for item in extract_citations_from_stream(tokens, llm_docs, doc_id_to_rank_map):
    #     if isinstance(item, CitationInfo):
    #         citation_info = item

    if citation_info:
        return Citation.from_llm_docs(llm_docs, extracted_id=citation_info.document_id)
    else:
        return Citation.from_llm_docs(llm_docs)
