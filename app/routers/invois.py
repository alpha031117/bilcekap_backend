from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.schemas.invois import TokenResponse, InvoiceSubmitRequest
from app.services.myinvois_service import myinvois_auth_service
from app.core.database import get_db
from app.models.taxpayer import Taxpayer
from datetime import datetime
from app.schemas.taxpayer import TaxpayerValidationResponse


router = APIRouter()


@router.post("/token", response_model=TokenResponse, summary="Fetch MyInvois OAuth token")
async def get_myinvois_token() -> TokenResponse:
    # Use credentials from environment (.env)
    data = await myinvois_auth_service.fetch_token()
    return TokenResponse(**data)


@router.get("/documents/{document_id}", summary="Get invoice/document by ID")
async def get_document(document_id: str):
    return await myinvois_auth_service.get_document_by_id(document_id)


@router.get("/taxpayer/validate/{tin}", response_class=PlainTextResponse, summary="Validate TIN via MyInvois and save status")
async def validate_tin(
    tin: str,
    idType: str = Query(..., description="Identification type e.g. NRIC, PASSPORT, BRN, ARMY"),
    idValue: str = Query(..., description="Identification value (e.g., NRIC number)"),
    db: Session = Depends(get_db)
):
    result = await myinvois_auth_service.validate_taxpayer_tin(tin, idType, idValue)
    is_valid = bool(result.get("valid", False))
    message = result.get("message", "Validation completed")

    # Upsert into local DB
    existing = db.query(Taxpayer).filter(Taxpayer.tin == tin).first()
    if existing:
        existing.id_type = idType
        existing.id_value = idValue
        existing.is_valid = is_valid
        existing.updated_at = datetime.utcnow()
        db.commit()
    else:
        new_row = Taxpayer(tin=tin, id_type=idType, id_value=idValue, is_valid=is_valid)
        db.add(new_row)
        db.commit()

    if is_valid:
        return f"TIN Number: {tin}\nID Type: {idType}\nID Value: {idValue}\nStatus: Active"
    return f"TIN Number: {tin}\nID Type: {idType}\nID Value: {idValue}\nStatus: INVALID ({message})"


@router.post("/documents/submit", summary="Submit invoice to MyInvois")
async def submit_invoice(payload: InvoiceSubmitRequest, db: Session = Depends(get_db)):
    # Build seller from taxpayer by seller_tin
    seller = db.query(Taxpayer).filter(Taxpayer.tin == payload.seller_tin).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller taxpayer not found")

    seller_name = seller.business_name or seller.full_name or ""
    seller_address = {
        "street": seller.address_street or "",
        "city": seller.address_city or "",
        "postcode": seller.address_postcode or "",
        "state": seller.address_state or "",
        "countryCode": seller.address_country_code or "MY",
    }

    # Try to look up buyer TIN by name and address (optional)
    buyer_row = db.query(Taxpayer).filter(
        (Taxpayer.full_name == payload.buyer_name) &
        (Taxpayer.address_street == payload.buyer_address.street) &
        (Taxpayer.address_city == payload.buyer_address.city) &
        (Taxpayer.address_postcode == payload.buyer_address.postcode) &
        (Taxpayer.address_state == payload.buyer_address.state)
    ).first()

    buyer_dict = {
        "tin": buyer_row.tin if buyer_row else None,
        "name": payload.buyer_name,
        "address": payload.buyer_address.model_dump(),
    }

    document_payload = {
        "documentType": "INVOICE",
        "invoice": {
            "seller": {
                "tin": payload.seller_tin,
                "name": seller_name,
                "address": seller_address,
            },
            "buyer": buyer_dict,
            "documentNumber": payload.documentNumber,
            "issueDate": payload.issueDate,
            "itemList": [i.model_dump() for i in payload.itemList],
            "totalAmount": payload.totalAmount,
            "currency": payload.currency,
            "taxDetails": [t.model_dump() for t in payload.taxDetails],
            "paymentTerms": payload.paymentTerms,
            "remarks": payload.remarks,
        },
    }

    # Remove None buyer tin if not found
    if document_payload["invoice"]["buyer"]["tin"] is None:
        document_payload["invoice"]["buyer"].pop("tin")

    return await myinvois_auth_service.submit_document(document_payload)

