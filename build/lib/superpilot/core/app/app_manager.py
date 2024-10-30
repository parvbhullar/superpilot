import logging
from collections import OrderedDict




class QueryProcessor:
    def __init__(self, query):
        self.query = query

    def predict_query_type(self):
        # Logic to predict query type from the original code
        return predict_question_type(self.query)

    def get_content(self, ai_persona):
        # Original get_content logic
        ...

    def generate_prompt(self, ai_persona, query_type, use_history=False):
        # Original generate_prompt logic using self.query, query_type, and ai_persona
        ...


class TaskManager:
    def __init__(self, thread_id, user, query):
        self.thread_id = thread_id
        self.user = user
        self.query = query
        self.query_processor = QueryProcessor(query)
        self.current_subtasks = OrderedDict()

    def create_task(self):
        # Logic for task creation
        ...

    def process_tasks(self):
        # Logic to process tasks (refactored from original code)
        ...

    def update_task_status(self, task_id, status):
        # Logic to update task status
        ...
