from abc import ABC
from typing import Dict, List, Optional

from pydantic import Field

from superpilot.core.planning.schema import (
    LanguageModelClassification,
)
from superpilot.core.planning.settings import PromptStrategyConfiguration
from superpilot.core.planning.strategies.simple import SimplePrompt
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.resource.model_providers import (
    SchemaModel,
)


class Address(SchemaModel):
    Type: str = Field(..., description="Type of the address (e.g., residential, office, etc.)")
    Address: str = Field(..., description="Full address")
    Reported_Date: str = Field(..., description="Date when the address was reported")
    Residence_Code: str = Field(..., description="Code representing the residence type")


class Consumer(SchemaModel):
    Name: str = Field(..., description="Name of the consumer")
    Date_of_Birth: str = Field(..., description="Consumer's date of birth")
    Gender: str = Field(..., description="Gender of the consumer")
    PAN: str = Field(..., description="Permanent Account Number of the consumer")
    Drivers_License: Optional[str] = Field(None, description="Driver's License of the consumer")
    UID: Optional[str] = Field(None, description="Aadhaar/UID number of the consumer")
    CKYC: Optional[str] = Field(None, description="CKYC number of the consumer")
    Mobile_Phones: List[str] = Field(..., description="List of mobile phone numbers of the consumer")
    Emails: List[str] = Field(..., description="List of email addresses of the consumer")
    Addresses: List[Address] = Field(..., description="List of addresses associated with the consumer")


class PaymentHistory(SchemaModel):
    Date: str = Field(..., description="Date of payment history record")
    Days_Past_Due: str = Field(..., description="Number of days the payment is past due")


class Loan(SchemaModel):
    Type: str = Field(..., description="Type of loan (e.g., personal loan, home loan, etc.)")
    Ownership: str = Field(..., description="Ownership type (e.g., individual, joint, etc.)")
    Opened: str = Field(..., description="Date when the loan was opened")
    Last_Payment: str = Field(..., description="Date of the last payment made")
    Closed: Optional[str] = Field(None, description="Date when the loan was closed, if applicable")
    Sanctioned: float = Field(..., description="Sanctioned amount for the loan")
    Current_Balance: float = Field(..., description="Current outstanding balance for the loan")
    Credit_Limit: Optional[float] = Field(None, description="Credit limit, if applicable")
    Cash_Limit: Optional[float] = Field(None, description="Cash limit, if applicable")
    Actual_Payment: Optional[float] = Field(None, description="Actual payment made")
    EMI: Optional[float] = Field(None, description="Equated Monthly Installment (EMI) amount")
    Payment_History: List[PaymentHistory] = Field(..., description="Payment history for the loan")


class ExtractLoanInfoParams(SchemaModel):
    Consumer: Consumer = Field(..., description="Consumer information details")
    Loans: List[Loan] = Field(..., description="List of loans associated with the consumer")


class ExtractLoanInfoPrompt(SimplePrompt, ABC):
    DEFAULT_SYSTEM_PROMPT = """
       Please extract all available loan information and present it in JSON format. Ensure that no details are omitted, including but not limited to the following fields: loan ID, borrower name, loan amount, interest rate, loan term, start date, payment schedule, status, and any other relevant information. If there are nested structures or related entities, include them appropriately within the JSON.
    """

    DEFAULT_USER_PROMPT_TEMPLATE = """
        {task_objective}
    """

    DEFAULT_PARSER_SCHEMA = ExtractLoanInfoParams.function_schema()

    default_configuration = PromptStrategyConfiguration(
        model_classification=LanguageModelClassification.SMART_MODEL,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
        parser_schema=DEFAULT_PARSER_SCHEMA,
    )

    def __init__(
            self,
            model_classification: LanguageModelClassification = default_configuration.model_classification,
            system_prompt: str = default_configuration.system_prompt,
            user_prompt_template: str = default_configuration.user_prompt_template,
            parser_schema: Dict = None,
    ):
        self._model_classification = model_classification
        self._system_prompt_message = system_prompt
        self._user_prompt_template = user_prompt_template
        self._parser_schema = parser_schema

    @property
    def model_classification(self) -> LanguageModelClassification:
        return self._model_classification

    def parse_response_content(
            self,
            response_content: dict,
    ) -> dict:
        """Parse the actual text response from the objective model.

        Args:
            response_content: The raw response content from the objective model.

        Returns:
            The parsed response.

        """
        # print(response_content)
        parsed_response = json_loads(response_content["function_call"]["arguments"])
        # print(response_content)
        # parsed_response = json_loads(response_content["content"])
        # parsed_response = self._parser_schema.from_response(response_content)
        return parsed_response

