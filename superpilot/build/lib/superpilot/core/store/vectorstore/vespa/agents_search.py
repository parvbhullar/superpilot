import requests
from queue import Queue
from concurrent.futures import ThreadPoolExecutor


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
          "query": "what was the manhattan project?",
          "yql": "select * from sources * where userQuery()"
        }

        return search_query

    def search_in_api(self, search_query):
        """
        Sends the query via HTTP to the search API and retrieves the most suitable agent documents.

        :param search_query: The constructed search query to be sent via HTTP.
        :return: A list of agent documents (hits) returned by the API.
        """
        try:
            # Send POST request to the API with the search query
            response = requests.post(self.api_url, json=search_query)
            response.raise_for_status()  # Raise an error for bad status codes
            # Assuming the API returns a JSON response with hits (agent docs)
            return response.json().get("root", {}).get("children", [])
        except requests.exceptions.RequestException as e:
            print(f"Error during API request: {e}")
            return []

    def create_paginated_queue(self, agent_docs, query):
        """
        Organizes the retrieved agent documents into a paginated queue.
        Each page will have 3 agents that will be processed in parallel.

        :param agent_docs: List of agent documents retrieved from the API.
        :return: A Queue object containing the agents.
        """
        q = Queue()
        for agent in agent_docs:
            agent['query'] = query
            q.put(agent)
        self.queue = q

    def execute_agents_parallel(self, agent_batch):
        """
        Executes the agents' answer generation function in parallel.

        :param agent_batch: A list of agents to be executed in parallel.
        :return: A list of results from the agents.
        """
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(lambda agent: self.simulate_agent_execution(agent), agent_batch))
        return results

    def simulate_agent_execution(self, agent):
        """
        Simulates the execution of an agent. This function should be replaced with
        the actual agent execution logic in a real-world scenario.

        :param agent: The agent document.
        :return: A simulated result from the agent.
        """
        q = agent.get("query", "QQ")
        # Simulate an agent's "execute" function (to be replaced with actual logic)
        print("Agent searching", agent)
        return {
            "agent_name": agent.get("persona_name", "Unknown"),
            "response": f"Simulated response for query {q} from {agent.get('persona_name', 'Unknown')}"
        }

    def paginate_and_execute(self):
        """
        Executes agents in batches of 'page_size' and generates answers.

        :return: A list of paginated results.
        """
        page_results = []
        while not self.queue.empty():
            # Get the next batch of agents (up to `page_size`)
            agent_batch = [self.queue.get() for _ in range(min(self.page_size, self.queue.qsize()))]

            # Execute the agents in parallel and get the results
            results = self.execute_agents_parallel(agent_batch)

            # Store the results for this page
            page_results.append(results)

            # Prompt user to decide whether to fetch next page
            user_input = input("Do you want to see the next page? (y/n): ")
            if user_input.lower() != 'y':
                break

        return page_results

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

        # Step 3: Create paginated queue
        self.create_paginated_queue(agent_docs, query)

        # Step 4: Paginate and execute agents
        results = self.paginate_and_execute()

        return results

    @classmethod
    def test(cls, query):
        # Example usage of the system with an API endpoint
        api_url = "http://localhost:8081/search/"  # Replace with the actual API URL

        # Instantiate the search system
        agent_search_system = AgentSearchSystem(api_url)

        # Run the search system with a user's query
        results = agent_search_system.run(query)

        # Output the results
        for page_result in results:
            for agent_result in page_result:
                print(agent_result)


# Example usage of the AgentSearchSystem
if __name__ == "__main__":
    user_query = "What are the most important historical events?"
    AgentSearchSystem.test(user_query)