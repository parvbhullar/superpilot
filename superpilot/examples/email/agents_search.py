import asyncio

import requests
from queue import Queue
from concurrent.futures import ThreadPoolExecutor


# from super.apps.ais_app.retrieve.vector_service import SearchDoc
# from super.apps.ais_app.search.postprocessing.postprocessing import semantic_reranking, rerank_chunks
#from superpilot.core.context.schema import Message
from pydantic import BaseModel


class AIAgent:
    """
    Model representing an AI agent with details about its identity, background, and knowledge base.
    """
    persona_name: str
    about: str
    tags: list[str] | None
    handle: str
    persona: str
    questions: list[str] | None
    score: float | None
    embeddings: list[float] | None

    def __init__(self, data):
        self.persona_name = data.get("persona_name")
        self.tags = data.get("tags", [])
        self.handle = data.get("handle")
        self.about = data.get("about")
        self.persona = data.get("persona")
        self.knowledge_bases = data.get("knowledge_bases", [])
        self.questions = data.get("questions", [])
        self.score = data.get("score", 0)
        self.embeddings = data.get("embeddings", None)


    def __str__(self):
        return f"AIAgent('{self.persona_name}', handle='{self.handle}', tags={self.persona_name}, score={self.score})"

    def display_info(self):
        """Prints a formatted summary of the agent's information."""
        print(f"Name: {self.persona_name}")
        print(f"Handle: {self.handle}")
        print("Tags:", ", ".join(self.tags))
        print("About:", self.about)
        print("Persona:", self.persona)
        print("Knowledge Bases:", ", ".join(self.knowledge_bases))

    def to_dict(self):
        return {
            "persona_name": self.persona_name,
            "tags": self.tags,
            "handle": self.handle,
            "about": self.about,
            "persona": self.persona,
            "knowledge_bases": self.knowledge_bases,
            "questions": self.questions,
            "score": self.score,
            "embeddings": self.embeddings
        }


class AgentSearchSystem:
    def __init__(self, api_url, page_size=3):
        """
        Initializes the Agent Search System with an API URL.

        :param api_url: The URL endpoint of the Vespa or search API.
        :param page_size: Number of agents to execute per page (default is 3).
        """
        self.api_url = api_url
        self.page_size = page_size
        self.queue = None

    def process_user_query(self, user_query):
        """
        Processes the user's input query and prepares the search request for the API.

        :param user_query: The input query from the user.
        :return: A dictionary containing the search query to be sent via HTTP request.
        """

        # Example placeholder function for generating a query embedding from user query
        def get_query_embedding(query):
            # This should return a tensor embedding representation for the query
            return [0.1, 0.2, 0.3]  # Placeholder for demonstration purposes

        # Construct Vespa search query
        search_query = {
            "yql": "select * from sources * where ([{\"targetHits\": 10}]nearestNeighbor(embedding, query_embedding));",
            "hits": 10,
            "offset": 0,
            "ranking": "hybrid_searchVARIABLE_DIM",
            "attributes": ["persona_name", "about", "questions", "boost", "embeddings"],
            "ranking.features": {
                "query(query_embedding)": get_query_embedding(user_query)
            },
            "ranking.profile": "default",
            "alpha": 0.7,
            "persona_about_ratio": 0.5
        }

        search_query = {
          "query": user_query,
          "yql": "select * from sources * where userQuery()"
        }

        search_query = {
            "query": user_query,
        }

        return search_query

    def search_in_api(self, search_query, offset=0, limit=5):
        """
        Sends the query via HTTP to the search API and retrieves the most suitable agent documents.

        :param offset:
        :param hits:
        :param search_query: The constructed search query to be sent via HTTP.
        :return: A list of agent documents (hits) returned by the API.
        """
        try:
            # Direct Vespa API call
            # return self.direct_vespa(limit, offset, search_query)
            url = self.api_url + f"?page_size={limit}"
            if offset > 0:
                url += f"&page={offset}"
            # Direct Search API calls
            response = requests.post(url,
                                     json=search_query)  # Search API
            response.raise_for_status()  
            agents = []
            for item in response.json().get("data", []):
                metadata = item["metadata"]
                agent = AIAgent(metadata)
                agents.append(agent)
            return agents
        except requests.exceptions.RequestException as e:
            print(f"Error during API request: {e}")
            return []

    # def direct_vespa(self, limit, offset, search_query):
    #     # Send POST request to the API with the search query
    #     response = requests.post(self.api_url + f"?offset={offset}&hits={limit}", json=search_query)  # Vespa
    #     response.raise_for_status()  # Raise an error for bad status codes
    #     # Assuming the API returns a JSON response with hits (agent docs)
    #     # return response.json().get("root", {}).get("children", [])
    #     return response.json().get("root", {}).get("children", [])


    # def search_agents(self, message: Message, offset=0, limit=5):
    #     # Step 1: Process user query
    #     search_query = self.process_user_query(message.message)

    #     # Step 2: Search via API for agent documents
    #     agent_docs = self.search_in_api(search_query, offset=offset, limit=limit)

    #     #agent_docs = self.rerank_agents(message, agent_docs)
    #     agents = [AIAgent(doc.metadata) for doc in agent_docs]
    #     return agents

    def run(self, query):
        """
        Main function that runs the entire agent search system workflow.

        :param query: User's search query.
        :return: Results of the agent executions.
        """
        # Step 1: Process user query
        search_query = self.process_user_query(query)

        # Step 2: Search via API for agent documents
        agent_docs = self.search_in_api(search_query)

        return agent_docs

    # def rerank_agents(self, message: Message, agent_docs):
    #     # Placeholder function for reranking agents based on user message
    #     agent_docs = rerank_chunks(message, agent_docs)
    #     return agent_docs

    @classmethod
    def test(cls, query, api_url = "http://localhost:8081/search/"):
        # Example usage of the system with an API endpoint
          # Replace with the actual API URL

        # Instantiate the search system
        agent_search_system = AgentSearchSystem(api_url)

        # Run the search system with a user's query
        results = agent_search_system.run(query)

        # Output the results
        for page_result in results:
            for agent_result in page_result:
                print("Agent Name:", agent_result["agent_name"])
                print(agent_result)
                print("=" * 50)


# Example usage of the AgentSearchSystem
if __name__ == "__main__":
    user_query = "What are the most important historical events?"
    AgentSearchSystem.test(user_query)