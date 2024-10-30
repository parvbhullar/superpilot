from collections.abc import Iterator
from typing import cast
from uuid import uuid4

from langchain.schema.messages import BaseMessage
from langchain_core.messages import AIMessageChunk
from langchain_core.messages import HumanMessage

from superpilot.core.store.chat.chat_utils import llm_doc_from_inference_section
from superpilot.core.store.chat.chat_models import AnswerQuestionPossibleReturn
from superpilot.core.store.chat.chat_models import CitationInfo
from superpilot.core.store.chat.chat_models import UnpodAnswerPiece
from superpilot.core.store.chat.chat_models import LlmDoc
from superpilot.examples.persona.answering.models import AnswerStyleConfig
from superpilot.examples.persona.answering.models import PreviousMessage
from superpilot.examples.persona.answering.models import PromptConfig
from superpilot.examples.persona.answering.models import StreamProcessor
from superpilot.examples.answering.prompts.build import AnswerPromptBuilder
from superpilot.examples.answering.prompts.build import default_build_system_message
from superpilot.examples.answering.prompts.build import default_build_user_message
from superpilot.examples.answering.prompts.citations_prompt import (
    build_citations_system_message,
)
from superpilot.examples.answering.prompts.citations_prompt import build_citations_user_message
from superpilot.examples.answering.prompts.quotes_prompt import build_quotes_user_message
from superpilot.examples.answering.stream_processing.citation_processing import (
    build_citation_processor,
)
from superpilot.examples.answering.stream_processing.quotes_processing import (
    build_quotes_processor,
)

def _get_answer_stream_processor(
    context_docs: list[LlmDoc],
    search_order_docs: list[LlmDoc],
    answer_style_configs: AnswerStyleConfig,
) -> StreamProcessor:
    if answer_style_configs.citation_config:
        return build_citation_processor(
            context_docs=context_docs, search_order_docs=search_order_docs
        )
    if answer_style_configs.quotes_config:
        return build_quotes_processor(
            context_docs=context_docs, is_json_prompt=not (QA_PROMPT_OVERRIDE == "weak")
        )

    raise RuntimeError("Not implemented yet")

AnswerStream = Iterator[AnswerQuestionPossibleReturn]

class Answer:
    def __init__(
        self,
        question: str,
        answer_style_config: AnswerStyleConfig,
        llm: LLM,
        prompt_config: PromptConfig,
        message_history: list[PreviousMessage] | None = None,
        single_message_history: str | None = None,
        files: list[LlmDoc] | None = None,
        skip_explicit_tool_calling: bool = False,
        return_contexts: bool = False,
    ) -> None:
        if single_message_history and message_history:
            raise ValueError(
                "Cannot provide both `message_history` and `single_message_history`"
            )

        self.question = question
        self.file_id_to_file = {file.file_id: file for file in (files or [])}
        self.tools = []
        self.force_use_tool = None
        self.skip_explicit_tool_calling = skip_explicit_tool_calling

        self.message_history = message_history or []
        self.single_message_history = single_message_history

        self.answer_style_config = answer_style_config
        self.prompt_config = prompt_config

        self.llm = llm

        self._final_prompt: list[BaseMessage] | None = None
        self._streamed_output: list[str] | None = None
        self._processed_stream: list[AnswerQuestionPossibleReturn] | None = None

        self._return_contexts = return_contexts

    def _update_prompt_builder_for_search_tool(
        self, prompt_builder: AnswerPromptBuilder, final_context_documents: list[LlmDoc]
    ) -> None:
        if self.answer_style_config.citation_config:
            prompt_builder.update_system_prompt(
                build_citations_system_message(self.prompt_config)
            )
            prompt_builder.update_user_prompt(
                build_citations_user_message(
                    question=self.question,
                    prompt_config=self.prompt_config,
                    context_docs=final_context_documents,
                    all_doc_useful=(
                        self.answer_style_config.citation_config.all_docs_useful
                        if self.answer_style_config.citation_config
                        else False
                    ),
                )
            )
        elif self.answer_style_config.quotes_config:
            prompt_builder.update_user_prompt(
                build_quotes_user_message(
                    question=self.question,
                    context_docs=final_context_documents,
                    history_str=self.single_message_history or "",
                    prompt=self.prompt_config,
                )
            )

    # Additional methods (_raw_output_for_explicit_tool_calling_llms, _raw_output_for_non_explicit_tool_calling_llms, etc.) remain unchanged

    @property
    def processed_streamed_output(self) -> AnswerStream:
        if self._processed_stream is not None:
            yield from self._processed_stream
            return

        output_generator = (
            self._raw_output_for_explicit_tool_calling_llms()
            if explicit_tool_calling_supported(
                self.llm.config.model_provider, self.llm.config.model_name
            )
            and not self.skip_explicit_tool_calling
            else self._raw_output_for_non_explicit_tool_calling_llms()
        )

        # Processing stream logic remains unchanged...

    @property
    def llm_answer(self) -> str:
        answer = ""
        for packet in self.processed_streamed_output:
            if isinstance(packet, UnpodAnswerPiece) and packet.answer_piece:
                answer += packet.answer_piece

        return answer

    @property
    def citations(self) -> list[CitationInfo]:
        citations: list[CitationInfo] = []
        for packet in self.processed_streamed_output:
            if isinstance(packet, CitationInfo):
                citations.append(packet)

        return citations