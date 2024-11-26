# models.py

from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.chains.conversation.memory import ConversationBufferWindowMemory


template = """
    {history}
    Human: {human_input}
    Assistant:"""

prompt = PromptTemplate(
    input_variables=["history", "human_input"], 
    template=template
)

chatgpt_chain = LLMChain(
    llm=OpenAI(temperature=0), 
    prompt=prompt, 
    verbose=True, 
    memory=ConversationBufferWindowMemory(k=2),
)

def generate_response(user_message: str) -> str:
    """Generate a response using Langchain."""
    return chatgpt_chain.predict(human_input=user_message)
