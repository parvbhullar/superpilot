from abc import ABC

from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning.strategies.simple import SimplePrompt

from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt,
)
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.resource.model_providers import (
    LanguageModelFunction,
    LanguageModelMessage,
    MessageRole,
    SchemaModel,
)
from superpilot.core.planning.settings import PromptStrategyConfiguration
from typing import Dict, Optional
import enum

from pydantic import Field
from typing import List


class InvoiceType(str, enum.Enum):
    Complete = "complete"
    Incomplete = "incomplete"
    Spam = "spam"
    Cannot_Be_Fixed = "cannot_be_fixed"


class SupplyType(str, enum.Enum):
    Complete = "complete"
    Incomplete = "incomplete"
    Spam = "spam"
    Cannot_Be_Fixed = "cannot_be_fixed"


class Item(SchemaModel):
    """
    Class representing an item in the itemList.
    """
    hsn_code: str = Field(..., description="HSN or SAC of Goods or Services as per Invoice line items")
    quantity: float = Field(..., description="Quantity of goods sold")
    unit_of_product: str = Field(..., description="UQC (Unit of Measure) of goods sold")
    gst_rate: float = Field(..., description="GST Rate that is applicable on the goods or services supplied")
    cess_amount: float = Field(..., description="Cess Amount as per invoice")
    taxable_value: float = Field(..., description="Taxable value of Goods or Service as per invoice, taking into account discount or abatement, if any")
    cgst_amount: float = Field(..., description="CGST Amount as per invoice")
    sgst_amount: float = Field(..., description="SGST Amount as per invoice")
    igst_amount: float = Field(..., description="IGST Amount as per invoice")
    item_description: str = Field(..., description="Description of goods sold")
    product_name: str = Field(..., description="Name of the product")
    invoice_value: float = Field(..., description="Value of the invoice for the item")


class Document(SchemaModel):
    """
    Class representing the data structure for document-related information.
    """
    document_number: str = Field(..., description="Document Number")
    document_date: str = Field(..., description="Document Date in format DD-MM-YYYY")
    original_document_number: Optional[str] = Field(None, description="Original Document Number that was before the voucher number was amended")
    original_document_date: Optional[str] = Field(None, description="Original Document date that was before the voucher number was amended")
    ref_document_number: Optional[str] = Field(None, description="Reference Document Number")
    ref_document_date: Optional[str] = Field(None, description="Reference Document Date")
    supply_type: str = Field(..., description="Specify the type of supply that was made")
    invoice_status: str = Field(..., description="Flag for deleting, holding or modifying an invoice")
    invoice_category: str = Field(..., description="Category of the invoice")
    invoice_type: str = Field(..., description="Invoice Type")
    total_invoice_value: float = Field(..., description="Supplier Invoice Value indicating a total of taxable value and total tax")
    total_taxable_value: float = Field(..., description="Taxable value of Goods or Service as per invoice, taking into account discount or abatement, if any")
    txpd_taxtable_value: float = Field(..., description="Taxable value as per tax table")
    shipping_bill_number: Optional[str] = Field(None, description="Shipping Bill Number")
    shipping_bill_date: Optional[str] = Field(None, description="Shipping Bill Date")
    reason: Optional[str] = Field(None, description="Reason for the document")
    port_code: Optional[str] = Field(None, description="Port Code")
    location: str = Field(..., description="Location code")
    gstr1_return_period: Optional[str] = Field(None, description="gstr1 return period in format MM-YYYY")
    gstr3b_return_period: Optional[str] = Field(None, description="3B auto-fill period in format MMYYYY")
    reverse_charge: Optional[str] = Field(None, description="If reverse charge is applicable on the supplies made to an unregistered business OR supplies made attract reverse charge")
    isamended: Optional[str] = Field(None, description="Specifies if a sale was revised")
    amended_pos: Optional[str] = Field(None, description="Amended place of supply")
    amended_period: Optional[str] = Field(None, description="Amended Period")
    place_of_supply: str = Field(..., description="Name of the state where supplies were actually made")
    supplier_gstin: str = Field(..., description="GSTIN/UID of the Supplier taxpayer/UN, Govt Bodies")
    buyer_gstin: str = Field(..., description="GSTIN/UID of the Receiver taxpayer/UN, Govt Bodies")
    customer_name: str = Field(..., description="Name of the customer to whom supplies were made")
    amortised_cost: str = Field(..., description="Amortised cost flag")
    itemList: List[Item] = Field(..., description="List of items in the document")


class DataList(SchemaModel):
    """
    Container class representing a tree of questions to ask a question answer system.
    and its dependencies. Make sure every question is in the tree, and every question is asked only once.
    """

    documents: List[Document] = Field(
        ..., description="List of gstr documents/rows to be processed"
    )


class GSTR1DataTransformerPrompt(SimplePrompt, ABC):
    DEFAULT_SYSTEM_PROMPT = """
        you are a GST expert. You need to analyze the data and provide the correct data & their respective fields such as status.

        Examples :-
        

        """

    DEFAULT_USER_PROMPT_TEMPLATE = """
        Content: {task_objective}

        -----
        Please use the above input as the content for the json generation.
        """

    DEFAULT_PARSER_SCHEMA = DataList.function_schema()

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

