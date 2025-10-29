from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.models.taxpayer import Taxpayer
from app.schemas.taxpayer import TaxpayerValidationResponse, TaxpayerInDB, TaxpayerCreate, TaxpayerUpdate
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


@router.post("/", response_model=TaxpayerInDB)
async def create_taxpayer(payload: TaxpayerCreate, db: Session = Depends(get_db)):
    # Force new entries to be invalid by default (is_valid = False)
    new_row = Taxpayer(
        tin=payload.tin,
        id_type=payload.id_type,
        id_value=payload.id_value,
        is_valid=False,
        business_name=payload.business_name,
        full_name=payload.full_name,
        address_street=payload.address_street,
        address_city=payload.address_city,
        address_postcode=payload.address_postcode,
        address_state=payload.address_state,
        address_country_code=payload.address_country_code,
    )
    db.add(new_row)
    db.commit()
    db.refresh(new_row)
    return new_row


@router.put("/{tin}", response_model=TaxpayerInDB)
async def update_taxpayer(tin: str, payload: TaxpayerUpdate, db: Session = Depends(get_db)):
    row = db.query(Taxpayer).filter(Taxpayer.tin == tin).first()
    if not row:
        raise HTTPException(status_code=404, detail="Taxpayer not found")
    # Update mutable fields if provided
    if payload.id_type is not None:
        row.id_type = payload.id_type
    if payload.id_value is not None:
        row.id_value = payload.id_value
    if payload.is_valid is not None:
        row.is_valid = payload.is_valid
    if payload.business_name is not None:
        row.business_name = payload.business_name
    if payload.full_name is not None:
        row.full_name = payload.full_name
    if payload.address_street is not None:
        row.address_street = payload.address_street
    if payload.address_city is not None:
        row.address_city = payload.address_city
    if payload.address_postcode is not None:
        row.address_postcode = payload.address_postcode
    if payload.address_state is not None:
        row.address_state = payload.address_state
    if payload.address_country_code is not None:
        row.address_country_code = payload.address_country_code
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row
