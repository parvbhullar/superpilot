import abc
import enum
import json
import os
from datetime import datetime, time
from typing import List, Any, Dict
import logging
import platform
from abc import ABC

import distro

from superpilot.core.configuration import SystemConfiguration
from superpilot.core.pilot.base import BasePilot
from superpilot.core.pilot.settings import PilotConfiguration, ExecutionNature
from superpilot.core.planning import LanguageModelClassification, LanguageModelResponse, PromptStrategy
from superpilot.core.planning.settings import LanguageModelConfiguration
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.plugin.utlis import load_class
from superpilot.core.resource.model_providers import LanguageModelProvider, OpenAIModelName, OPEN_AI_MODELS
from superpilot.core.resource.model_providers.factory import ModelProviderFactory, ModelConfigFactory
from superpilot.examples.persona.prompt import PersonaPrompt
from superpilot.examples.persona.schema import Message, Context
from superpilot.examples.persona.vector_service import Retriever, ServiceRM
from superpilot.framework.llm import count_string_tokens
import inflection
from superpilot.examples.persona.answering.simple_answer import SimpleAnswer
# from superpilot.examples.persona.answering.new_answer import Answer
SEARCH_SERVICE_URL = os.getenv("SEARCH_SERVICE_URL")

class RoleConfiguration(SystemConfiguration):
    name: str
    role: str
    creation_time: str
    cycle_count: int
    max_task_cycle_count: int

class HandlerConfiguration(SystemConfiguration):
    """Struct for model configuration."""
    location: PluginLocation
    role: RoleConfiguration = None
    execution_nature: ExecutionNature = ExecutionNature.AUTO
    models: Dict[LanguageModelClassification, LanguageModelConfiguration] = {}
    callbacks: List[PluginLocation] = None
    prompt_strategy: SystemConfiguration = None
    memory_provider_required: bool = False
    workspace_required: bool = False


class BaseHandler(abc.ABC):
    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    async def execute(self, *args, **kwargs):
        ...

    # @abc.abstractmethod
    # async def observe(self, *args, **kwargs):
    #     ...

    @abc.abstractmethod
    def __repr__(self):
        ...

    @classmethod
    def name(cls) -> str:
        """The name of the ability."""
        return inflection.underscore(cls.__name__)

    @abc.abstractmethod
    def dump(self):
        ...
class PersonaAgent(BaseHandler, ABC):
    """A class representing a handler step."""

    default_configuration = HandlerConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="super.apps.ais_app.agents.base.PersonaHandler",
        ),
        role=RoleConfiguration(
            name="persona_agent",
            role="A agent to handle user queries based on given persona.",
            cycle_count=0,
            max_task_cycle_count=3,
            creation_time=datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
        ),
        execution_nature=ExecutionNature.AUTO,
    )

    def __init__(
            self,
            configuration: HandlerConfiguration = default_configuration,
            logger: logging.Logger = logging.getLogger(__name__),
            model_providers: Dict[str, LanguageModelProvider] = None,
            session_id: str = None,
            
    ) -> None:
        self._session_id = session_id
        self._logger = logger
        self._configuration = configuration
        self._execution_nature = configuration.execution_nature
        self._agent_data = {}

        self._providers: Dict[LanguageModelClassification, LanguageModelProvider] = {}
        if model_providers is None:
            model_providers = ModelProviderFactory.load_providers()
        for model, model_config in self._configuration.models.items():
            self._providers[model] = model_providers[model_config.provider_name]

        prompt_config = self._configuration.prompt_strategy.dict()
        location = prompt_config.pop("location", None)
        if location is not None:
            self._prompt_strategy = load_class(location, prompt_config)
        else:
            self._prompt_strategy = PersonaPrompt(**prompt_config)

        self.retriever = Retriever(rm=ServiceRM(SEARCH_SERVICE_URL))
        self.simple_answer = None


    async def execute(
        self, objective: str | Message, *args, **kwargs
    ) -> LanguageModelResponse:
        """Execute the task."""
        self._logger.debug(f"Executing task: {objective}")
        if not isinstance(objective, Message):
            # if task is not passed, one is created with default settings
            task = Message.create(message=objective)
        else:
            task = objective
        context = kwargs.get('context', None)
        if len(args) > 0:
            context = args[0]
        if context is None:
            context = Context(task.session_id, [task])

        context_res = await self.exec_task(task, context, **kwargs)
        return context_res


    async def exec_task(self, message: Message, context:Context, **kwargs) -> LanguageModelResponse:
        ## TODO fetch data from store service from those knowledge bases and update the template_kwargs
        # Call the retriever on a particular query.
        kn_bases = self._agent_data.get('knowledge_bases',
                                        ['U83Y7PIIL1CICBT6LTVKNXRA'])  # TODO remove hardcoded knowledge base
        info = self.retriever.search(message.message, kn_bases=[kn_bases])
        question = message.message
        docs=message.data
        persona = self._agent_data
        template_kwargs = message.generate_kwargs()
        template_kwargs.update(kwargs)
        template_kwargs['gathered_information'] = info
        template_kwargs['context'] = context.summary()
        #self.simple_answer = Answer(question=question, llm=self._providers[LanguageModelClassification.SMART_MODEL], files=docs)
        self.simple_answer=SimpleAnswer(question=question, llm=self._providers[LanguageModelClassification.SMART_MODEL],docs=docs,persona=persona)
        # Get the answer using SimpleAnswer
        answer = self.simple_answer.llm_answer

        # Return the answer in LanguageModelResponse format
        #return LanguageModelResponse(content=answer)
        return (answer)


        # return await self.chat_with_model(
        #     self._prompt_strategy,
        #     **template_kwargs,
        # )

    async def chat_with_model(
        self,
        prompt_strategy: PromptStrategy,
        **kwargs,
    ) -> LanguageModelResponse:
        model_classification = prompt_strategy.model_classification
        model_configuration = self._configuration.models[model_classification]

        template_kwargs = self._make_template_kwargs_for_strategy(prompt_strategy)
        kwargs.update(template_kwargs)
        prompt = prompt_strategy.build_prompt(
            model_name=model_configuration.model_name, **kwargs
        )
        # print("Prompt", prompt)
        model_configuration = self.choose_model(
            model_classification, model_configuration, prompt
        )

        model_configuration = model_configuration.dict()
        self._logger.debug(f"Using model configuration: {model_configuration}")
        del model_configuration["provider_name"]
        provider = self._providers[model_classification]
        if "response_format" in kwargs:
            model_configuration["response_format"] = kwargs["response_format"]

        self._logger.debug(f"Using prompt:\n{prompt}\n\n")
        response = await provider.create_language_completion(
            model_prompt=prompt.messages,
            functions=prompt.functions,
            function_call=prompt.get_function_call(),
            # req_res_callback=(
            #     self._callback.model_req_res_callback if self._callback else None
            # ),
            **model_configuration,
            completion_parser=prompt_strategy.parse_response_content,
        )

        return LanguageModelResponse.parse_obj(response.dict())

    def choose_model(self, model_classification, model_configuration, prompt):
        if model_configuration.model_name not in [
            OpenAIModelName.GPT3,
            OpenAIModelName.GPT4,
        ]:
            return model_configuration
        current_tokens = count_string_tokens(
            str(prompt), model_configuration.model_name
        )
        print("Tokens", current_tokens)
        token_limit = OPEN_AI_MODELS[model_configuration.model_name].max_tokens
        completion_token_min_length = 1000
        send_token_limit = token_limit - completion_token_min_length
        if current_tokens > send_token_limit:
            if model_classification == LanguageModelClassification.FAST_MODEL:
                model_configuration.model_name = OpenAIModelName.GPT4_O_MINI
            elif model_classification == LanguageModelClassification.SMART_MODEL:
                print("Using GPT4_TURBO")
                model_configuration.model_name = OpenAIModelName
        return model_configuration

    def _make_template_kwargs_for_strategy(self, strategy: PromptStrategy):
        provider = self._providers[strategy.model_classification]
        template_kwargs = {
            "os_info": get_os_info(),
            "api_budget": provider.get_remaining_budget(),
            "current_time": datetime.strftime(datetime.now(), "%c"),
        }
        return template_kwargs

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __str__(self):
        return self._configuration.__str__()

    def name(self) -> str:
        """The name of the ability."""
        return self._configuration.role.name

    def dump(self) -> dict:
        role_config = self._configuration.role
        dump = {
            "name": role_config.name,
            "role": role_config.role,
            "agent_data": self._agent_data,
            #"docs":docs,
            # "prompt_strategy": self._prompt_strategy.get_config().__dict__
        }
        return dump

    @classmethod
    def from_json(cls, json_data: str|dict) -> "PersonaAgent":
        if isinstance(json_data, dict):
            data = json_data
        else:
            data = json.loads(json_data)
        fields = data.get('fields', data)

        models_config = ModelConfigFactory.get_models_config(
            smart_model_name=fields.get('smart_model_name', OpenAIModelName.GPT4_O_MINI),
            fast_model_name=fields.get('fast_model_name', OpenAIModelName.GPT4),
            smart_model_temp=fields.get('smart_model_temp', 0.2),
            fast_model_temp=fields.get('fast_model_temp', 0.2),
        )
        #combined_content = "\n".join([clean_content(d['content']) for d in data['data']])

        #print("Combined Content")
        #print(combined_content)
        query=data['query']
        #user_prompt = ("user query:"+query+"\n"+"gathered information:"+combined_content+"\n")



        # user_prompt={
        #             'gathered_information':data["data"],
        #             'user_query':data["query"]}
        

        system_prompt = (PersonaPrompt.DEFAULT_SYSTEM_PROMPT + "\\n"
                         + fields.get('about', '')
                         + "\\n" + fields.get('persona', ''))
        
        prompt_strategy = PersonaPrompt.factory(
            system_prompt=system_prompt,
            user_prompt_template=PersonaPrompt.DEFAULT_USER_PROMPT_TEMPLATE
            #user_prompt_template=user_prompt
        )

        configuration = HandlerConfiguration(
            location=PluginLocation(
                storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                storage_route="super.apps.ais_app.pilot.base.PersonaHandler",
            ),
            role=RoleConfiguration(
                name=fields.get('persona_name', ''),
                role=fields.get('about', ''),
                cycle_count=0,
                max_task_cycle_count=3,
                creation_time=datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
            ),
            execution_nature=ExecutionNature.AUTO,
            models=models_config,
            prompt_strategy=prompt_strategy.get_config(),
        )

        instance = cls(configuration)
        instance._agent_data = fields
        return instance


def get_os_info() -> str:
    os_name = platform.system()
    os_info = (
        platform.platform(terse=True)
        if os_name != "Linux"
        else distro.name(pretty=True)
    )
    return os_info



def clean_content(content):
    # Remove extra spaces
    cleaned = content.strip()
    # Replace '{' and '}' with empty strings
    cleaned = cleaned.replace('{', '').replace('}', '')
    return cleaned


# from superpilot.examples.persona.answering import Answer,SimpleAnswer
# from superpilot.examples.persona.answering import _get_answer_stream_processor
# docs=[]
# context_docs=_get_answer_stream_processor(context_docs=docs)


# def stream_chat_message_objects(
#     new_msg_req: CreateChatMessageRequest,
#     user: None,
#     db_session: Session,
#     # Needed to translate persona num_chunks to tokens to the LLM
#     default_num_chunks: float = MAX_CHUNKS_FED_TO_CHAT,
#     # For flow with search, don't include as many chunks as possible since we need to leave space
#     # for the chat history, for smaller models, we likely won't get MAX_CHUNKS_FED_TO_CHAT chunks
#     max_document_percentage: float = CHAT_TARGET_CHUNK_PERCENTAGE,
#     # if specified, uses the last user message and does not create a new user message based
#     # on the `new_msg_req.message`. Currently, requires a state where the last message is a
#     # user message (e.g. this can only be used for the chat-seeding flow).
#     use_existing_user_message: bool = False,
#     litellm_additional_headers: dict[str, str] | None = None,
# ) -> ChatPacketStream:
#     """Streams in order:
#     1. [conditional] Retrieved documents if a search needs to be run
#     2. [conditional] LLM selected chunk indices if LLM chunk filtering is turned on
#     3. [always] A set of streamed LLM tokens or an error anywhere along the line if something fails
#     4. [always] Details on the final AI response message that is created

#     """
#     try:
#         user_id = user.id if user is not None else None

#         # chat_session = get_chat_session_by_id(
#         #     chat_session_id=new_msg_req.chat_session_id,
#         #     user_id=user_id,
#         #     db_session=db_session,
#         # )

#         message_text = new_msg_req.message
#         chat_session_id = new_msg_req.chat_session_id
#         parent_id = new_msg_req.parent_message_id
#         reference_doc_ids = new_msg_req.search_doc_ids
#         retrieval_options = new_msg_req.retrieval_options
#         #persona = chat_session.persona

#         prompt_id = new_msg_req.prompt_id
#         if prompt_id is None and persona.prompts:
#             prompt_id = sorted(persona.prompts, key=lambda x: x.id)[-1].id

#         if reference_doc_ids is None and retrieval_options is None:
#             raise RuntimeError(
#                 "Must specify a set of documents for chat or specify search options"
#             )

#         try:
#             llm = get_llm_for_persona(
#                 persona=persona,
#                 llm_override=new_msg_req.llm_override or chat_session.llm_override,
#                 additional_headers=litellm_additional_headers,
#             )
#         except GenAIDisabledException:
#             raise RuntimeError("LLM is disabled. Can't use chat flow without LLM.")

#         llm_tokenizer = get_default_llm_tokenizer()
#         llm_tokenizer_encode_func = cast(
#             Callable[[str], list[int]], llm_tokenizer.encode
#         )

#         embedding_model = get_current_db_embedding_model(db_session)
#         document_index = get_default_document_index(
#             primary_index_name=embedding_model.index_name, secondary_index_name=None
#         )

#         # Every chat Session begins with an empty root message
#         root_message = get_or_create_root_message(
#             chat_session_id=chat_session_id, db_session=db_session
#         )

#         if parent_id is not None:
#             parent_message = get_chat_message(
#                 chat_message_id=parent_id,
#                 user_id=user_id,
#                 db_session=db_session,
#             )
#         else:
#             parent_message = root_message

#         user_message = None
#         if not use_existing_user_message:
#             # Create new message at the right place in the tree and update the parent's child pointer
#             # Don't commit yet until we verify the chat message chain
#             user_message = create_new_chat_message(
#                 chat_session_id=chat_session_id,
#                 parent_message=parent_message,
#                 prompt_id=prompt_id,
#                 message=message_text,
#                 token_count=len(llm_tokenizer_encode_func(message_text)),
#                 message_type=MessageType.USER,
#                 files=None,  # Need to attach later for optimization to only load files once in parallel
#                 db_session=db_session,
#                 commit=False,
#             )
#             # re-create linear history of messages
#             final_msg, history_msgs = create_chat_chain(
#                 chat_session_id=chat_session_id, db_session=db_session
#             )
#             if final_msg.id != user_message.id:
#                 db_session.rollback()
#                 raise RuntimeError(
#                     "The new message was not on the mainline. "
#                     "Be sure to update the chat pointers before calling this."
#                 )

#             # NOTE: do not commit user message - it will be committed when the
#             # assistant message is successfully generated
#         else:
#             # re-create linear history of messages
#             final_msg, history_msgs = create_chat_chain(
#                 chat_session_id=chat_session_id, db_session=db_session
#             )
#             if final_msg.message_type != MessageType.USER:
#                 raise RuntimeError(
#                     "The last message was not a user message. Cannot call "
#                     "`stream_chat_message_objects` with `is_regenerate=True` "
#                     "when the last message is not a user message."
#                 )

#         # load all files needed for this chat chain in memory
#         files = load_all_chat_files(
#             history_msgs, new_msg_req.file_descriptors, db_session
#         )
#         latest_query_files = [
#             file
#             for file in files
#             if file.file_id in [f["id"] for f in new_msg_req.file_descriptors]
#         ]

#         if user_message:
#             attach_files_to_chat_message(
#                 chat_message=user_message,
#                 files=[
#                     new_file.to_file_descriptor() for new_file in latest_query_files
#                 ],
#                 db_session=db_session,
#                 commit=False,
#             )

#         selected_db_search_docs = None
#         selected_llm_docs: list[LlmDoc] | None = None
#         if reference_doc_ids:
#             identifier_tuples = get_doc_query_identifiers_from_model(
#                 search_doc_ids=reference_doc_ids,
#                 chat_session=chat_session,
#                 user_id=user_id,
#                 db_session=db_session,
#             )

#             # Generates full documents currently
#             # May extend to include chunk ranges
#             selected_llm_docs = inference_documents_from_ids(
#                 doc_identifiers=identifier_tuples,
#                 document_index=document_index,
#             )
#             document_pruning_config = DocumentPruningConfig(
#                 is_manually_selected_docs=True
#             )

#             # In case the search doc is deleted, just don't include it
#             # though this should never happen
#             db_search_docs_or_none = [
#                 get_db_search_doc_by_id(doc_id=doc_id, db_session=db_session)
#                 for doc_id in reference_doc_ids
#             ]

#             selected_db_search_docs = [
#                 db_sd for db_sd in db_search_docs_or_none if db_sd
#             ]

#         else:
#             document_pruning_config = DocumentPruningConfig(
#                 max_chunks=int(
#                     persona.num_chunks
#                     if persona.num_chunks is not None
#                     else default_num_chunks
#                 ),
#                 max_window_percentage=max_document_percentage,
#                 use_sections=new_msg_req.chunks_above > 0
#                 or new_msg_req.chunks_below > 0,
#             )

#         # Cannot determine these without the LLM step or breaking out early
#         partial_response = partial(
#             create_new_chat_message,
#             chat_session_id=chat_session_id,
#             parent_message=final_msg,
#             prompt_id=prompt_id,
#             # message=,
#             # rephrased_query=,
#             # token_count=,
#             message_type=MessageType.ASSISTANT,
#             # error=,
#             # reference_docs=,
#             db_session=db_session,
#             commit=False,
#         )

#         if not final_msg.prompt:
#             raise RuntimeError("No Prompt found")

#         prompt_config = PromptConfig.from_model(
#             final_msg.prompt,
#             prompt_override=(
#                 new_msg_req.prompt_override or chat_session.prompt_override
#             ),
#         )

#         # find out what tools to use
#         search_tool: SearchTool | None = None
#         tool_dict: dict[int, list[Tool]] = {}  # tool_id to tool
#         for db_tool_model in persona.tools:
#             # handle in-code tools specially
#             if db_tool_model.in_code_tool_id:
#                 tool_cls = get_built_in_tool_by_id(db_tool_model.id, db_session)
#                 if tool_cls.__name__ == SearchTool.__name__ and not latest_query_files:
#                     search_tool = SearchTool(
#                         db_session=db_session,
#                         user=user,
#                         persona=persona,
#                         retrieval_options=retrieval_options,
#                         prompt_config=prompt_config,
#                         llm=llm,
#                         pruning_config=document_pruning_config,
#                         selected_docs=selected_llm_docs,
#                         chunks_above=new_msg_req.chunks_above,
#                         chunks_below=new_msg_req.chunks_below,
#                         full_doc=new_msg_req.full_doc,
#                     )
#                     tool_dict[db_tool_model.id] = [search_tool]
#                 elif tool_cls.__name__ == ImageGenerationTool.__name__:
#                     dalle_key = None
#                     if (
#                         llm
#                         and llm.config.api_key
#                         and llm.config.model_provider == "openai"
#                     ):
#                         dalle_key = llm.config.api_key
#                     else:
#                         llm_providers = fetch_existing_llm_providers(db_session)
#                         openai_provider = next(
#                             iter(
#                                 [
#                                     llm_provider
#                                     for llm_provider in llm_providers
#                                     if llm_provider.provider == "openai"
#                                 ]
#                             ),
#                             None,
#                         )
#                         if not openai_provider or not openai_provider.api_key:
#                             raise ValueError(
#                                 "Image generation tool requires an OpenAI API key"
#                             )
#                         dalle_key = openai_provider.api_key
#                     tool_dict[db_tool_model.id] = [
#                         ImageGenerationTool(api_key=dalle_key)
#                     ]

#                 continue

#             # handle all custom tools
#             if db_tool_model.openapi_schema:
#                 tool_dict[db_tool_model.id] = cast(
#                     list[Tool],
#                     build_custom_tools_from_openapi_schema(
#                         db_tool_model.openapi_schema
#                     ),
#                 )

#         tools: list[Tool] = []
#         for tool_list in tool_dict.values():
#             tools.extend(tool_list)

#         # factor in tool definition size when pruning
#         document_pruning_config.tool_num_tokens = compute_all_tool_tokens(tools)
#         document_pruning_config.using_tool_message = explicit_tool_calling_supported(
#             llm.config.model_provider, llm.config.model_name
#         )

#         # LLM prompt building, response capturing, etc.
#         answer = Answer(
#             question=final_msg.message,
#             latest_query_files=latest_query_files,
#             answer_style_config=AnswerStyleConfig(
#                 citation_config=CitationConfig(
#                     all_docs_useful=selected_db_search_docs is not None
#                 ),
#                 document_pruning_config=document_pruning_config,
#             ),
#             prompt_config=prompt_config,
#             llm=(
#                 llm
#                 or get_llm_for_persona(
#                     persona=persona,
#                     llm_override=new_msg_req.llm_override or chat_session.llm_override,
#                     additional_headers=litellm_additional_headers,
#                 )
#             ),
#             message_history=[
#                 PreviousMessage.from_chat_message(msg, files) for msg in history_msgs
#             ],
#             tools=tools,
#             force_use_tool=(
#                 _check_should_force_search(new_msg_req)
#                 if search_tool and len(tools) == 1
#                 else None
#             ),
#         )

#         reference_db_search_docs = None
#         qa_docs_response = None
#         ai_message_files = None  # any files to associate with the AI message e.g. dall-e generated images
#         dropped_indices = None
#         tool_result = None
#         for packet in answer.processed_streamed_output:
#             if isinstance(packet, ToolResponse):
#                 if packet.id == SEARCH_RESPONSE_SUMMARY_ID:
#                     (
#                         qa_docs_response,
#                         reference_db_search_docs,
#                         dropped_indices,
#                     ) = _handle_search_tool_response_summary(
#                         packet=packet,
#                         db_session=db_session,
#                         selected_search_docs=selected_db_search_docs,
#                         # Deduping happens at the last step to avoid harming quality by dropping content early on
#                         dedupe_docs=retrieval_options.dedupe_docs
#                         if retrieval_options
#                         else False,
#                     )
#                     yield qa_docs_response
#                 elif packet.id == SECTION_RELEVANCE_LIST_ID:
#                     chunk_indices = packet.response

#                     if reference_db_search_docs is not None and dropped_indices:
#                         chunk_indices = drop_llm_indices(
#                             llm_indices=chunk_indices,
#                             search_docs=reference_db_search_docs,
#                             dropped_indices=dropped_indices,
#                         )

#                     yield LLMRelevanceFilterResponse(
#                         relevant_chunk_indices=chunk_indices
#                     )
#                 elif packet.id == IMAGE_GENERATION_RESPONSE_ID:
#                     img_generation_response = cast(
#                         list[ImageGenerationResponse], packet.response
#                     )

#                     file_ids = save_files_from_urls(
#                         [img.url for img in img_generation_response]
#                     )
#                     ai_message_files = [
#                         FileDescriptor(id=str(file_id), type=ChatFileType.IMAGE)
#                         for file_id in file_ids
#                     ]
#                     yield ImageGenerationDisplay(
#                         file_ids=[str(file_id) for file_id in file_ids]
#                     )
#                 elif packet.id == CUSTOM_TOOL_RESPONSE_ID:
#                     custom_tool_response = cast(CustomToolCallSummary, packet.response)
#                     yield CustomToolResponse(
#                         response=custom_tool_response.tool_result,
#                         tool_name=custom_tool_response.tool_name,
#                     )

#             else:
#                 if isinstance(packet, ToolCallFinalResult):
#                     tool_result = packet
#                 yield cast(ChatPacket, packet)

#     except Exception as e:
#         logger.exception("Failed to process chat message")

#         # Don't leak the API key
#         error_msg = str(e)
#         if llm.config.api_key and llm.config.api_key.lower() in error_msg.lower():
#             error_msg = (
#                 f"LLM failed to respond. Invalid API "
#                 f"key error from '{llm.config.model_provider}'."
#             )

#         yield StreamingError(error=error_msg)
#         # Cancel the transaction so that no messages are saved
#         db_session.rollback()
#         return

#     # Post-LLM answer processing
#     try:
#         db_citations = None
#         if reference_db_search_docs:
#             db_citations = translate_citations(
#                 citations_list=answer.citations,
#                 db_docs=reference_db_search_docs,
#             )

#         # Saving Gen AI answer and responding with message info
#         tool_name_to_tool_id: dict[str, int] = {}
#         for tool_id, tool_list in tool_dict.items():
#             for tool in tool_list:
#                 tool_name_to_tool_id[tool.name()] = tool_id

#         gen_ai_response_message = partial_response(
#             message=answer.llm_answer,
#             rephrased_query=(
#                 qa_docs_response.rephrased_query if qa_docs_response else None
#             ),
#             reference_docs=reference_db_search_docs,
#             files=ai_message_files,
#             token_count=len(llm_tokenizer_encode_func(answer.llm_answer)),
#             citations=db_citations,
#             error=None,
#             tool_calls=[
#                 ToolCall(
#                     tool_id=tool_name_to_tool_id[tool_result.tool_name],
#                     tool_name=tool_result.tool_name,
#                     tool_arguments=tool_result.tool_args,
#                     tool_result=tool_result.tool_result,
#                 )
#             ]
#             if tool_result
#             else [],
#         )
#         db_session.commit()  # actually save user / assistant message

#         msg_detail_response = translate_db_message_to_chat_message_detail(
#             gen_ai_response_message
#         )

#         yield msg_detail_response
#     except Exception as e:
#         logger.exception(e)

#         # Frontend will erase whatever answer and show this instead
#         yield StreamingError(error="Failed to parse LLM output")