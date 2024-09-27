import json
import os
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.core.store.vectorstore.vespa.app_generator import VespaAppGenerator

# Example Usage
if __name__ == "__main__":
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
    response = app_generator.deploy(app_path="vespa/ai_agents")
    print(response)

    # Sample data to feed into Vespa
    documents = [
        {
            "id": "id:my_application:new_schema::1",
            "fields": {
                "control_objective_external": "Ensure data integrity",
                "vendor_comments_response_important_please_answer_the_following": "No issues found",
                "column": "Security",
                "id": 1,
                "task": "Audit logs",
                "client": "Client A",
                "area": "IT",
                "country": "USA",
                "contact": "John Doe",
                "assignee": "Jane Smith",
                "completion": "75%",
                "start_date": "2021-01-01",
                "deadline": "2021-06-30",
                "budget": "$5000",
                "transaction_type": "Internal",
                "account": "Account123",
                "version": "v2.1",
                "available": "Yes"
            }
        },
        {
            "id": "id:my_application:new_schema::2",
            "fields": {
                "control_objective_external": "Maintain system availability",
                "vendor_comments_response_important_please_answer_the_following": "System uptime is 99%",
                "column": "Operations",
                "id": 2,
                "task": "System monitoring",
                "client": "Client B",
                "area": "Operations",
                "country": "Canada",
                "contact": "Alice Brown",
                "assignee": "Bob Johnson",
                "completion": "90%",
                "start_date": "2021-02-15",
                "deadline": "2021-08-15",
                "budget": "$8000",
                "transaction_type": "External",
                "account": "Account456",
                "version": "v3.0",
                "available": "No"
            }
        }
        # Add more documents as needed
    ]

    # Feed documents into Vespa
    for doc in documents:
        response = app.feed_document(document=doc)
        print("Feed response:", response.json())

    # Define a query to search for documents containing the word "system"
    query_result = app.query(body={
        'yql': 'select * from sources * where userQuery()',
        'query': 'system',
        'type': 'all',
        'ranking': 'default'
    })

    # Print the query result
    print("Query result:")
    print(json.dumps(query_result.json, indent=2))

    # Stop the Vespa Docker container when done
    # vespa_docker.stop()