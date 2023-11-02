import autogen
import os

config_list = autogen.config_list_from_json(
    "superpilot/tests/OAI_CONFIG_LIST",
    filter_dict={
        "model": {
            "gpt-4",
            "gpt4",
            "gpt-4-32k",
            "gpt-4-32k-0314",
            "gpt-4-32k-v0314",
        }
    }
)

from autogen.agentchat.contrib.math_user_proxy_agent import MathUserProxyAgent

autogen.ChatCompletion.start_logging()

# 1. create an AssistantAgent instance named "assistant"
assistant = autogen.AssistantAgent(
    name="assistant",
    system_message="You are a helpful assistant.",
    llm_config={
        "request_timeout": 600,
        "seed": 42,
        "config_list": config_list,
    }
)

# 2. create the MathUserProxyAgent instance named "mathproxyagent"
# By default, the human_input_mode is "NEVER", which means the agent will not ask for human input.
mathproxyagent = MathUserProxyAgent(
    name="mathproxyagent",
    human_input_mode="NEVER",
    code_execution_config={"use_docker": False},
)

WOLFRAM_APP_ID = os.environ.get("MATHPIX_APP_ID")

# math_problem = "Find all $x$ that satisfy the inequality $(2x+10)(x+3)<(3x+9)(x+8)$. Express your answer in interval notation."
# mathproxyagent.initiate_chat(assistant, problem=math_problem)


math_problem = "Find all numbers $a$ for which the graph of $y=x^2+a$ and the graph of $y=ax$ intersect. Express your answer in interval notation."

query = """
    1. Step 1: State the Null Hypothesis. ...
    2. Step 2: State the Alternative Hypothesis....
    3. Step 3: Set. ...
    4. Step 4: Collect Data. ...
    5. Step 5: Calculate a test statistic....
    (o) Show Transcribed Text
    For each test below, submit your answers to steps mathbf1 through mathbf5 of the significance testing process. In steos 4 and 5 , explain why you chose that answer.
    3. Test if the population mean years of education (EDUC) is more than 12. Submit your answers to steps mathbf1 through mathbf5 of the significance testing process.
    One-sample mathrmt test
     begintabular|c|c|c|c|c|c|c|
     hline Variable     Obs     Mean     Std. Err.     Std. Dev.     [95 
     hline educ     2,345     13.73177     .0614208     2.974313     13.61133     13.85221   
     hline  multicolumn4|c| mean = mean ( educ )             =28.1952   
     hline  multicolumn4|c| Ho: mean =12     degrees     of freedom =     =2344   
     hline
     endtabular

    Ha: mean <12
    operatornamePr( mathrmT< mathrmt)=1.0000
    Ha: mean !=12
    operatornamePr(| mathrmT|>| mathrmt|)=0.0000
    Ha: mean > 12
    operatornamePr( mathrmT> mathrmt)=0.0000

    """

query = """
    In the complex numbers, where i^2=-1, which of the following is equal to the result of squaring the expression (i + 4)
        a. 4i
        b. 16i
        c. 15 + 8i
        d. i + 16
        e. 17-18i
    """


def format_messages(messages):
    messages = list(messages.values())[0]
    # Skip the first message and extract the 'content' from the rest
    contents = [msg['role'] + " : " + msg['content'] for msg in messages[1:]]

    # Join the contents with a space to form the prompt
    prompt = '\n\n'.join(contents)

    return prompt

mathproxyagent.initiate_chat(assistant, problem=query, prompt_type="python")

print("*" * 32, "Chatting", "*" * 32)
print(format_messages(mathproxyagent.chat_messages))





# mathproxyagent.initiate_chat(assistant, problem=math_problem, prompt_type="two_tools")