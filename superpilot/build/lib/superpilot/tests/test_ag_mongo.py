# Import necessary libraries and modules
import autogen
from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from typing import List, Dict, Union
from pymongo import MongoClient
import pymongo
import openai

# Load the configuration from JSON file
config_list = config_list_from_json(env_or_file="llm_config")


class MongoRetrieveUserProxyAgent(RetrieveUserProxyAgent):
    def query_vector_db(self, query_texts: List[str], n_results: int = 10, search_string: str = "", **kwargs) -> Dict[str, Union[List[str], List[List[str]]]]:
        # Combine all query texts into one string
        concatenated_text = " ".join(query_texts)

        # Fetch the embedding from MongoDB
        embedding = self.get_embedding(concatenated_text)

        # Retrieve similar documents from MongoDB
        documents = self.find_similar_documents(embedding)
        ids = [str(idx) for idx in range(1, len(documents) + 1)]
        document_contents = [document.get("text_chunks", "") for document in documents]
        return {
            "ids": [ids],  # Wrap ids in a list
            "documents": [document_contents],  # Wrap document_contents in a list
        }

    def retrieve_docs(self, problem: str, n_results: int = 20, search_string: str = "", **kwargs):
        # Query for similar documents
        results = self.query_vector_db(
            query_texts=[problem],
            n_results=n_results,
            search_string=search_string,
            **kwargs,
        )
        self._results = results

        # Check if results is a dictionary and "documents" is a list
        if isinstance(results["ids"], list) and len(results["ids"]) > 0 and isinstance(results["ids"][0], str):
            doc_id = results["ids"][0]
            if doc_id in self._doc_ids:
                # Access the "documents" key in the results dictionary
                for idx, document in enumerate(results["documents"]):
                    if isinstance(document, dict):
                        print(f"Document {idx + 1}: {document.get('text_chunks', '')}")
                    else:
                        print(f"Document {idx + 1}: {document}")
            else:
                print("No documents found.")

    def get_embedding(self, text, model="text-embedding-ada-002"):
        """
        Get the embedding for a given text using OpenAI's API.
        """
        text = text.replace("\n", " ")
        return openai.Embedding.create(input=[text], model=model)['data'][0]['embedding']

    def connect_db(self):
        """
        Connect to the MongoDB server and return the collection.
        """
        mongo_url = "db+srv://YOUR_LOGIN:YOUR_PASSWORD@YOUR_ATLAS_CLUSTER/test?retryWrites=true&w=majority"
        client = pymongo.MongoClient(mongo_url)
        db = client["YOUR_VECTOR_DB"]
        collection = db["YOUR_VECTOR_COLLECTION"]
        return collection

    def find_similar_documents(self, embedding):
        """
        Find similar documents in MongoDB based on the provided embedding.
        """
        collection = self.connect_db()
        documents = list(collection.aggregate([
            {
                "$search": {
                    "index": "YOUR_VECTOR_INDEX",
                    "knnBeta": {
                        "vector": embedding,
                        "path": "YOUR_EMBEDDING_FIELD",
                        "k": 10,
                    },
                }
            },
            {"$project": {"_id": 1, "text_chunks": 1}}
        ]))
        return documents


def run_db_agent(query):
    # Instantiate the Assistant Agent with provided configuration
    assistant = RetrieveAssistantAgent(
        name="assistant",
        system_message="You are a helpful assistant.",
        llm_config=config_list,
    )

    # Instantiate the User Proxy Agent with MongoDB functionality
    ragproxyagent = MongoRetrieveUserProxyAgent(
        name="MongoRAGproxyagent",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=2,
        retrieve_config={"task": "qa"},
    )
    # Reset the assistant and retrieve documents for a specific problem
    assistant.reset()
    ragproxyagent.initiate_chat(assistant, problem=query)


if __name__ == "__main__":
    run_db_agent(query="When mifid2 is created?")