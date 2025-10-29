import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.config import settings
import logging
from app.services.myinvois_service import myinvois_auth_service

logger = logging.getLogger(__name__)


class LHDNService:
    def __init__(self):
        self.base_url = settings.LHDN_API_URL
        self.timeout = settings.LHDN_API_TIMEOUT
        
    async def validate_taxpayer_tin(
        self, 
        tin: str, 
        id_type: str, 
        id_value: str
    ) -> Dict[str, Any]:
        """
        Validate taxpayer TIN using LHDN API
        
        Args:
            tin: Taxpayer Identification Number
            id_type: Type of identification (NRIC, PASSPORT, etc.)
            id_value: Value of the identification
            
        Returns:
            Dict containing validation result from LHDN API
            
        Raises:
            HTTPException: If API call fails
        """
        
        # Prepare the request payload
        payload = {
            "tin": tin,
            "idType": id_type,
            "idValue": id_value
        }
        
        # Prepare headers with MyInvois bearer token
        token = await myinvois_auth_service.get_valid_token()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1.0/taxpayer/validate/{tin}",
                    params={"idType": id_type, "idValue": id_value},
                    headers=headers
                )
                
                # Log the request for debugging
                logger.info(f"LHDN API request: {response.url}")
                logger.info(f"LHDN API response status: {response.status_code}")
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    # Taxpayer not found
                    return {
                        "valid": False,
                        "message": "Taxpayer not found in LHDN database",
                        "error_code": "TAXPAYER_NOT_FOUND"
                    }
                elif response.status_code == 400:
                    # Bad request - invalid format
                    return {
                        "valid": False,
                        "message": "Invalid TIN format or ID parameters",
                        "error_code": "INVALID_FORMAT"
                    }
                else:
                    # Other HTTP errors
                    logger.error(f"LHDN API error: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=502,
                        detail=f"LHDN API error: {response.status_code}"
                    )
                    
        except httpx.TimeoutException:
            logger.error("LHDN API timeout")
            raise HTTPException(
                status_code=504,
                detail="LHDN API timeout - service unavailable"
            )
        except httpx.RequestError as e:
            logger.error(f"LHDN API request error: {str(e)}")
            raise HTTPException(
                status_code=502,
                detail="Failed to connect to LHDN API"
            )
        except Exception as e:
            logger.error(f"Unexpected error calling LHDN API: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )


# Create a singleton instance
ldhn_service = LHDNService()
