from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.models.taxpayer import Taxpayer
from app.schemas.taxpayer import TaxpayerValidationResponse, TaxpayerInDB
from app.services.ldhn_service import ldhn_service

router = APIRouter()


def validate_tin_format(tin: str) -> bool:
    """
    Validate TIN format based on your business rules.
    This is a placeholder implementation - customize based on your requirements.
    """
    # Basic validation - TIN should be alphanumeric and reasonable length
    if not tin or len(tin) < 3 or len(tin) > 50:
        return False
    
    # Add more specific validation rules here based on your TIN format requirements
    return tin.isalnum() or tin.replace('-', '').replace('_', '').isalnum()


def validate_id_type_and_value(id_type: str, id_value: str) -> bool:
    """
    Validate ID type and value based on your business rules.
    This is a placeholder implementation - customize based on your requirements.
    """
    if not id_type or not id_value:
        return False
    
    # Example validation rules - customize based on your requirements
    valid_id_types = ['NRIC', 'PASSPORT', 'DRIVER_LICENSE', 'NATIONAL_ID']
    
    if id_type.upper() not in valid_id_types:
        return False
    
    # Basic ID value validation
    if len(id_value) < 2 or len(id_value) > 100:
        return False
    
    return True


@router.get("/validate/{tin}", response_model=TaxpayerValidationResponse)
async def validate_taxpayer_tin(
    tin: str,
    idType: str = Query(..., alias="idType", description="Type of identification"),
    idValue: str = Query(..., alias="idValue", description="Value of the identification"),
    db: Session = Depends(get_db)
):
    """
    Validate a taxpayer TIN using LHDN API with the provided identification type and value.
    
    Args:
        tin: Taxpayer Identification Number
        idType: Type of identification (e.g., 'NRIC', 'PASSPORT')
        idValue: Value of the identification
        
    Returns:
        TaxpayerValidationResponse: Validation result with details from LHDN API
    """
    
    # Basic format validation before calling LHDN API
    if not validate_tin_format(tin):
        return TaxpayerValidationResponse(
            tin=tin,
            id_type=idType,
            id_value=idValue,
            is_valid=False,
            validation_message="Invalid TIN format",
            validated_at=datetime.utcnow()
        )
    
    # Validate ID type and value
    if not validate_id_type_and_value(idType, idValue):
        return TaxpayerValidationResponse(
            tin=tin,
            id_type=idType,
            id_value=idValue,
            is_valid=False,
            validation_message="Invalid ID type or value",
            validated_at=datetime.utcnow()
        )
    
    try:
        # Call LHDN API for validation
        ldhn_result = await ldhn_service.validate_taxpayer_tin(tin, idType, idValue)
        
        # Extract validation result from LHDN API response
        is_valid = ldhn_result.get("valid", False)
        validation_message = ldhn_result.get("message", "Validation completed")
        
        # Check if taxpayer exists in our local database
        existing_taxpayer = db.query(Taxpayer).filter(Taxpayer.tin == tin).first()
        
        if existing_taxpayer:
            # Update existing record with LHDN validation result
            existing_taxpayer.id_type = idType
            existing_taxpayer.id_value = idValue
            existing_taxpayer.is_valid = is_valid
            existing_taxpayer.updated_at = datetime.utcnow()
            db.commit()
            
            return TaxpayerValidationResponse(
                tin=existing_taxpayer.tin,
                id_type=existing_taxpayer.id_type,
                id_value=existing_taxpayer.id_value,
                is_valid=existing_taxpayer.is_valid,
                validation_message=validation_message,
                validated_at=datetime.utcnow()
            )
        else:
            # Create new taxpayer record with LHDN validation result
            new_taxpayer = Taxpayer(
                tin=tin,
                id_type=idType,
                id_value=idValue,
                is_valid=is_valid
            )
            
            db.add(new_taxpayer)
            db.commit()
            db.refresh(new_taxpayer)
            
            return TaxpayerValidationResponse(
                tin=new_taxpayer.tin,
                id_type=new_taxpayer.id_type,
                id_value=new_taxpayer.id_value,
                is_valid=new_taxpayer.is_valid,
                validation_message=validation_message,
                validated_at=datetime.utcnow()
            )
            
    except HTTPException as e:
        # Re-raise HTTP exceptions from LHDN service
        raise e
    except Exception as e:
        # Handle any other unexpected errors
        return TaxpayerValidationResponse(
            tin=tin,
            id_type=idType,
            id_value=idValue,
            is_valid=False,
            validation_message=f"Validation failed due to internal error: {str(e)}",
            validated_at=datetime.utcnow()
        )


@router.get("/{tin}", response_model=TaxpayerInDB)
async def get_taxpayer(
    tin: str,
    db: Session = Depends(get_db)
):
    """
    Get taxpayer information by TIN.
    
    Args:
        tin: Taxpayer Identification Number
        
    Returns:
        TaxpayerInDB: Taxpayer information
    """
    taxpayer = db.query(Taxpayer).filter(Taxpayer.tin == tin).first()
    
    if not taxpayer:
        raise HTTPException(status_code=404, detail="Taxpayer not found")
    
    return taxpayer


@router.get("/", response_model=list[TaxpayerInDB])
async def list_taxpayers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    List all taxpayers with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List[TaxpayerInDB]: List of taxpayers
    """
    taxpayers = db.query(Taxpayer).offset(skip).limit(limit).all()
    return taxpayers
