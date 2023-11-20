import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))


class ThreadManager:
    def __init__(self):
        self.kafka_broker = "localhost:9092"

    def start_executor(self, block):
        goal = self.pop_from_queue(block)
        return self.execute_goal(goal)

    def execute_goal(self, goal):
        # Execute the task using SuperPilot
        superpilot = initialize_superpilot(goal)
        logger.info(f"Executing goal: {goal.goal} with stage: {goal.stage}", __class__.__name__)
        goal = superpilot.init_plan(goal)

        if goal.stage == ThreadStage.WAITING:
            # save the goal to the database
            logger.info(f"Saving goal: {goal.goal} with stage: {goal.stage}", __class__.__name__)
            goal = ThreadStore.save_goal_with_status(goal, Status.IN_PROGRESS, ThreadStage.TASK_PLANING_COMPLETED)
            # save_object_to_file("goal", goal, os.getcwd())

        if goal.stage != ThreadStage.COMPLETED:
            # push task actions to task execution queue for execution if distributed mode is true
            logger.info(f"CFG.distributed_mode is {CFG.distributed_mode}", __class__.__name__)
            if CFG.distributed_mode:
                self.push_to_queue(goal)
            else:
                # execute the actions locally
                task_executor = TaskExecutor(superpilot, goal)
                task_executor.start_executor()

    def push_to_queue(self, action):
        # Push action to the execution queue
        pass

    def pop_from_queue(self, block: Block):
        # Pop action from the execution queue

        # check for block in the database based on thread_id and text based on the current block
        block = block.get_initiate_block()
        goal_param = block.get_goal()
        data = ThreadStore.get_goal_by(goal_param)
        return data


def get_task(t, pilot_handle):
    task = ThreadSchema()
    task.goal = t
    task.id = "1"
    task.pilot_handle = pilot_handle
    task.thread_id = "532955534064615681"

    return task


def test_query_planner():
    import pandas as pd
    # Specify the path to your JSON file
    json_file_path = "../notebooks/data/self-instruct/databricks-dolly-15k.jsonl"
    # Open the JSON file
    df = pd.read_json(json_file_path, lines=True)
    # Now you can work with the DataFrame as desired
    # For example, you can display the first few rows
    print(df.columns)
    executor = ThreadExecutor()
    j = []
    for index, row in df.iterrows():
        # Access and print a specific column
        # print(row['instruction'])

        action_result = executor.start_executor(get_task(row['instruction'], 'question_pilot_01'))
        j.append({"instruction": row['instruction'], "query_plan": action_result})
        if index > 10:
            break

    jsonl_file_path = "logs/query_planner_response.json"
    df = pd.DataFrame(j)
    df.to_json(jsonl_file_path, orient='records')


def process_block(thread_id, pilot_handle):
    executor = ThreadExecutor()
    block = read_block(thread_id, pilot_handle)
    if not block:
        return None
    print(block)
    action_result = executor.start_executor(block)
    # return action_result


def manual_testing():
    executor = ThreadExecutor()
    # executor.start_executor(get_task("Find the best headphones for me."))
    # action_result = executor.start_executor(get_task("What is gst?", 'question_pilot_01'))  # how to deal with questions which requires answers from multiple sources?

    # executor.start_executor(get_task("Assign a task to the developer to fix a critical bug in the system."))  # TODO set correct expectations from the AI so correct understanding of these tasks created and so the correct workflow is generated
    # executor.start_executor(get_task("Analyze website traffic and user behavior using web analytics tools."))
    # executor.start_executor(get_task("Initiate the recruitment process for a senior HR manager position."))
    # executor.start_executor(get_task("Analyze market trends to identify potential product expansion opportunities."))
    # executor.start_executor(get_task("I want to create videos for my product, how to proceed"))
    # executor.start_executor(get_task("I want to create a website for my product, how to proceed"))
    # executor.start_executor(get_task("what is the best way to show html content in reactjs"))
    # executor.start_executor(get_task("how to use react-draft-wysiwyg in next.js"))
    # executor.start_executor(get_task("Remind me to pick up groceries at 5 PM today."))
    # action_result = executor.start_executor(get_task("Best Place to eat burger in Delhi", 'question_pilot_01'))
    # action_result = executor.start_executor(get_task("how to use react-draft-wysiwyg in next.js", 'question_pilot_01'))
    # action_result = executor.start_executor(get_task("Analyze website traffic and user behavior using web analytics tools.", 'question_pilot_01'))
    # action_result = executor.start_executor(get_task("Identify which instrument is string or percussion: Cantaro, Gudok. Also provide details definations for both", 'question_pilot_01'))
    # action_result = executor.start_executor(get_task("https://cremawork.com/ write an article for given website", 'question_pilot_01'))
    # action_result = executor.start_executor(get_task("Saving $10, 000 for a house down payment Social", 'question_pilot_01'))
    # action_result = executor.start_executor(get_task("Completing a 10 K race in under an hour", 'question_pilot_01'))
    # action_result = executor.start_executor(get_task("What is the difference in populations of Canada and the Jason's home country?", 'question_pilot_01'))
    # action_result = executor.start_executor(get_task("Find the best headphones for 20 years old female", 'question_pilot_01'))
    # action_result = executor.start_executor(get_task("Find market research reports on the competitor's product offerings", 'question_pilot_01'))
    # action_result = executor.start_executor(get_task("Find an available software library for implementing encryption algorithms.", 'question_pilot_01'))
    # action_result = executor.start_executor(get_task("Determine the opponent team in the game where Kyle Van Zyl scored 36 points", 'question_pilot_01'))
    # action_result = executor.start_executor(get_task("Initiate the recruitment process for a senior HR manager position", 'question_pilot_01'))
    # action_result = executor.start_executor(get_task("Write a patent on Multimodel Transformer it should able to execute the multi task models at once.", 'question_pilot_01'))
    action_result = executor.start_executor(get_task("Tell me weather of bikaner?", 'question_pilot_01'))
    # print(json.dumps(action_result, indent=4), "\n")
    # print("OutPut -->", action_result['output'], "\n")
    # Fitness: Completing a 10 K race in under an hour
    # Financial: Saving $10, 000 for a house down payment Social
    # Media: Gaining 10, 000 Instagram followers within six months
    # Learning: Achieving fluency in a new language within a year
    # Cooking: Mastering five gourmet recipes and hosting a dinner party for friends and family


def main():
    # manual_testing()
    # process_block('527154309490540801', 'question_pilot_01')
    from services.superpilot_service.services.task import process_task_plan
    block_data = {
        # "thread_id": "527154309490540801",
        "thread_id": "527154309490540801",
        "user": {
            "user_id": 89713833,
            "username": "anonymous",
            "email": "anonymous.89713833@unpod.tv",
            "first_name": "Anonymous",
            "last_name": "User",
            "user_token": "ANONYMOUS",
            "is_active": True,
            "full_name": "Anonymous User",
            "is_anonymous": True
        },
        "data": {
            "block": "html",
            "block_type": "question",
            "data": {"content": "Understand the current topics in Indian politics and write a blog on the same"},
            "parent_id": None,
            "pilot": "question_pilot_01"
        }
    }
    process_task_plan(**block_data)
    # test_query_planner()


if __name__ == "__main__":
    print("Executor class")
    # main()
    test_query_planner()