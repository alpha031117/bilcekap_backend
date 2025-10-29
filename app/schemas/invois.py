from pydantic import BaseModel
from typing import Optional, List


class TokenResponse(BaseModel):
    access_token: str
    expires_in: int
    token_type: str
    scope: str


class Address(BaseModel):
    street: str
    city: str
    postcode: str
    state: str
    countryCode: str


class Item(BaseModel):
    description: str
    quantity: float
    unitPrice: float
    totalAmount: float
    currency: str


class TaxDetail(BaseModel):
    taxType: str
    taxRate: float
    taxAmount: float


class InvoiceSubmitRequest(BaseModel):
    seller_tin: str
    buyer_name: str
    buyer_address: Address
    documentNumber: str
    issueDate: str
    itemList: List[Item]
    totalAmount: float
    currency: str
    taxDetails: List[TaxDetail]
    paymentTerms: str
    remarks: Optional[str] = None


