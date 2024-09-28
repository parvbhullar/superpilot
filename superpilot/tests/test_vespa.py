import json
import os
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


from superpilot.core.store.vectorstore.vespa.agents_search import AgentSearchSystem
from superpilot.core.store.vectorstore.vespa.agent_chunker import AIAgentChunker
from superpilot.core.store.vectorstore.vespa.app_generator import VespaAppGenerator


def deploy_app():

    # Sample JSON schema
    json_schema_str = """
    {
        "type" : "object",
        "properties" : {
            "control_objective_external" : {
                "type" : "string",
                "title" : "control_objective_external",
                "description" : "",
                "defaultValue" : ""
            },
            "vendor_comments_response_important_please_answer_the_following" : {
                "type" : "string",
                "title" : "vendor_comments_response_important_please_answer_the_following",
                "description" : "",
                "defaultValue" : ""
            }
        },
        "required" : []
    }
    """
    json_schema = json.loads(json_schema_str)

    # Application name
    application_name = "my_application"
    app_generator = VespaAppGenerator.factory(app_name=application_name, schema_name="agent_doc")
    # app_generator.generate_app(json_schema=json_schema)
    response = app_generator.deploy(app_path="vespa/ai_agents")

def index_jsonl_to_vespa(file_path: str):

    # Call the function to index records
    agent_chunker = AIAgentChunker(None, None)
    agent_chunker.index_jsonl_to_vespa(file_path)

    # Stop the Vespa Docker container when done
    #vespa_docker.stop()
    #vespa_docker.stop()

def search_vespa():
    user_query = "What are the most important historical events?"
    AgentSearchSystem.test(user_query)

# Example Usage
if __name__ == "__main__":
    # Deploy the Vespa application
    # deploy_app()

    # Index JSONL file to Vespa
    # index_jsonl_to_vespa("persona_output.jsonl")

    # Search Vespa
    search_vespa()