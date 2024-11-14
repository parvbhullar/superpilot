from typing import List

from superpilot.core.store.search.models import SearchDoc
from superpilot.examples.persona.schema import Message, User, Role, Context
from superpilot.examples.persona.schema import LanguageModelResponse


class AgentResponse:
    def __init__(self, message:Message, agent: User, response: LanguageModelResponse, context: Context = None, docs: List[SearchDoc] = None):
        self.message = message
        self.response = response
        self.context = context
        self.docs = docs
        self.agent = agent

    def __str__(self):
        return self.response

    def response_message(self):
        message = Message.from_model_response(self.response, self.message.session_id, self.agent, id=self.message.id)
        message.data = self.citations()
        return message

    def node_to_doc(self, node):
        return SearchDoc(
            document_id=node.node_id,
            content=node.text,
            metadata=node.metadata,
            blurb=node.metadata.get('blurb', ''),
            url=node.metadata.get('file_path', ''),
            score=node.score,
            source_type=node.metadata.get('source', ''),
            semantic_identifier=node.metadata.get('semantic_identifier', ''),
        )

    def citations(self):
        # Batch evaluation (optimizing this part by using get_eval in parallel)
        # score = get_eval(question=question, ground_truth=ground_truths, answer=answers)
        # print("Score List", score)

        citations = {}
        citation_num = {}
        ref_docs = []
        # Filter documents based on score > 0.20 and collect citations
        for idx, doc in enumerate(self.response.get("source_nodes", self.docs), start=1):
            # if score_value > 0.20:
            if not isinstance(doc, SearchDoc):
                doc = self.node_to_doc(doc)

            ref_docs.append(doc.to_dict())
            citations[str(idx)] = len(str(doc.content))  # Assuming 'content' size as a reference
            citation_num[str(idx)] = doc.document_id  # Use document_id for reference

        # docs = [
        #     {k: v for k, v in doc.items() if k != "content" and k != "metadata"}
        #     for doc in ref_docs
        # ]
        # for doc in docs:
        #     if "metadata" in doc and "main_content" in doc["metadata"]:
        #         del doc["metadata"]["main_content"]

        response = {
            'ref_docs': ref_docs,
            'citations': citations,
            "citation_num": citation_num,
            'followup_questions': [],
            'actions': [],
        }
        return response

