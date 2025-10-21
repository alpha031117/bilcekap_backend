from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TaxpayerValidationRequest(BaseModel):
    tin: str = Field(..., description="Taxpayer Identification Number")
    id_type: str = Field(..., description="Type of identification (e.g., 'NRIC', 'PASSPORT')")
    id_value: str = Field(..., description="Value of the identification")


class TaxpayerValidationResponse(BaseModel):
    tin: str
    id_type: str
    id_value: str
    is_valid: bool
    validation_message: str
    validated_at: datetime
    
    class Config:
        from_attributes = True


class TaxpayerCreate(BaseModel):
    tin: str = Field(..., min_length=1, max_length=50)
    id_type: str = Field(..., min_length=1, max_length=50)
    id_value: str = Field(..., min_length=1, max_length=100)
    is_valid: bool = True


class TaxpayerUpdate(BaseModel):
    is_valid: Optional[bool] = None
    id_type: Optional[str] = Field(None, max_length=50)
    id_value: Optional[str] = Field(None, max_length=100)


class TaxpayerInDB(TaxpayerCreate):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


