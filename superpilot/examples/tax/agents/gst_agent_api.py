import requests
from fastapi import FastAPI

from typing import Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from typing import Optional
from langchain import PromptTemplate
from langchain.chains import ConversationChain
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentType, initialize_agent
from langchain.utilities import SerpAPIWrapper
import os
from services.taxgptservice.api.config import settings

# os.environ["OPENAI_API_KEY"] = "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"
os.environ["SERPAPI_API_KEY"] = settings.SERP_API_KEY

llm_gpt4 = ChatOpenAI(temperature=0, streaming=True, model="gpt-4-1106-preview")

greeting_prompt_template = """Give a short warm greeting to the user. If user asks about your identity, then just tell them that you are an Artificial GST Agent.
{history}
Human:{input}"""
GREET_PROMPT = PromptTemplate(
    template=greeting_prompt_template, input_variables=["history", "input"]
)
greeting_conversation = ConversationChain(llm=llm_gpt4, prompt=GREET_PROMPT)


class GreetingTool(BaseTool):
    name = "greeting_agent"
    description = """useful for when user's message is greeting or when user asks about your identity. Input may containg words like 'Good Morning', 'Good Afternoon', 'Hello', 'Hi', 'Who are you?' etc."""

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        return greeting_conversation.run(query)

    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("greeting agent does not support async")


def reco_data_extract(buyer_gstin, reco_type, f_year):
    tok_response = requests.post(
        url="https://qa-arapback.mastersindia.co/api/v1/token-auth/",
        data={"username": "dhananjaysingh@mastersindia.co", "password": "Jcb@12345"},
    )

    response = requests.get(
        url="https://qa-arapback.mastersindia.co/api/v1/saas-apis/recoapi/?buyer_gstin="
        + buyer_gstin
        + "&reco_type="
        + reco_type
        + "&f_year="
        + f_year,
        headers={
            "Authorization": f"JWT {tok_response.json()['token']}",
            "Productid": "enterprises",
            "GSTIN": buyer_gstin,
        },
    )

    if response.status_code != 200:
        print(
            f"something went wrong from the reco api side with status code {response.status_code}"
        )
    return response.content.decode("utf-8")


class RecoDataExtractionInput(BaseModel):
    """Inputs for reco apis"""

    buyer_gstin: str = Field(description="Buyer GSTIN for reco api")
    reco_type: str = Field(
        description="Type of Reconciliation for reco api. If the input is GSTR2A consider it as '2A-PR' or if it is GSTR2B, consider it as '2B-PR'."
    )
    f_year: str = Field(description="Financial Year for reco api")


class RecoDataExtractionTool(BaseTool):
    name = "data_extract"
    description = """
      Useful when you want to get data regarding reconciliation.
      You should trigger the reco api url. Don't give the explaination, just give the api's response."""

    args_schema: Type[BaseModel] = RecoDataExtractionInput

    def _run(self, buyer_gstin: str, reco_type: str, f_year: str):
        data = reco_data_extract(buyer_gstin, reco_type, f_year)
        return data

    def _arun(self, buyer_gstin: str, reco_type: str, f_year: str):
        raise NotImplementedError("reco_data_extract does not support async")


def gstr1_summary(gstin, year, month):
    tok_response = requests.post(
        url="https://qa-arapback.mastersindia.co/api/v1/token-auth/",
        data={"username": "anshitmehrotra@mastersindia.co", "password": "Test@123"},
        headers={"GSTIN": gstin},
    )

    response = requests.get(
        url="https://qa-arapback.mastersindia.co/api/v1/saas-apis/get-gstr1-summary/",
        headers={
            "Authorization": f"JWT {tok_response.json()['token']}",
            "gstin": gstin,
            "year": year,
            "month": month,
        },
    )

    if response.status_code != 200:
        print(
            f"something went wrong from the saas api side with status code {response.status_code}"
        )
    return response.content.decode("utf-8")


class GSTR1SummaryInput(BaseModel):
    """Inputs for reco apis"""

    gstin: str = Field(description="GSTIN for saas api")
    year: str = Field(description="Financial Year for saas api. Ex- 2022-23,2020-21")
    month: str = Field(description="Financial Month for saas api")


class GSTR1SummaryTool(BaseTool):
    name = "gstr1_summary"
    description = """
      Useful when you want to get data regarding GSTR1 summary.
      You should trigger the saas api url. Don't give the explaination, just give the api's response."""

    args_schema: Type[BaseModel] = GSTR1SummaryInput

    def _run(self, gstin: str, year: str, month: str):
        data = gstr1_summary(gstin, year, month)
        return data

    def _arun(self, gstin: str, year: str, month: str):
        raise NotImplementedError("gstr1_summary does not support async")


class GoogleAssistantTool(BaseTool):
    search = SerpAPIWrapper()
    name = "google_assistant"
    description = """useful for when you need to answer questions that are current affairs, or when other Tools fails to answer."""

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        return self.search.run(query)

    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("google agent does not support async")


app = FastAPI()

tools = [
    GreetingTool(),
    RecoDataExtractionTool(),
    GSTR1SummaryTool(),
    GoogleAssistantTool(),
]

agent = initialize_agent(
    tools, llm_gpt4, agent=AgentType.OPENAI_FUNCTIONS, verbose=True
)


@app.post("/gst_agent")
def process_query(query: str):
    try:
        response = agent.run(query)
        output = {"success": True, "response": response, "error": ""}
        return output
    except Exception as e:
        output = {"success": False, "response": "", "error": str(e)}
        return output


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=1234)
