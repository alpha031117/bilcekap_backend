import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.config import settings
import logging
import time


logger = logging.getLogger(__name__)


class MyInvoisAuthService:
    def __init__(self) -> None:
        self.token_url = settings.MYINVOIS_TOKEN_URL
        self.api_base = settings.MYINVOIS_API_BASE
        # Use static values regardless of .env to avoid misconfiguration
        self.scope = "InvoicingAPI"
        self.grant_type = "client_credentials"
        self._access_token: Optional[str] = None
        self._expires_at_epoch: float = 0

    async def fetch_token(
        self,
        override_client_id: Optional[str] = None,
        override_client_secret: Optional[str] = None,
        override_scope: Optional[str] = None,
        override_grant_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        client_id = (override_client_id or settings.MYINVOIS_CLIENT_ID)
        client_secret = (override_client_secret or settings.MYINVOIS_CLIENT_SECRET)
        scope = (override_scope or self.scope)
        grant_type = (override_grant_type or self.grant_type)

        # Normalize to avoid hidden whitespace or quotes in .env
        client_id = client_id.strip().strip('"').strip("'") if client_id else client_id
        client_secret = client_secret.strip().strip('"').strip("'") if client_secret else client_secret
        scope = scope.strip() if scope else scope
        grant_type = grant_type.strip() if grant_type else grant_type

        if not client_id or not client_secret:
            raise HTTPException(status_code=500, detail="MyInvois client credentials not configured")

        form_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": grant_type,
            "scope": scope,
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            async with httpx.AsyncClient(timeout=settings.LHDN_API_TIMEOUT) as client:
                # Attempt 1: credentials in body
                response = await client.post(self.token_url, data=form_data, headers=headers)
                print(
                    "MyInvois token attempt1 status: %s (scope=%s grant=%s id_ends=%s)",
                    response.status_code,
                    scope,
                    grant_type,
                    (client_id[-4:] if client_id else None),
                )
                if response.status_code == 200:
                    data = response.json()
                    expires_in = int(data.get("expires_in", 0))
                    self._access_token = data.get("access_token")
                    self._expires_at_epoch = time.time() + max(0, expires_in - 30)
                    return data

                # Attempt 2 (fallback): HTTP Basic auth, without client_secret in body
                if response.status_code in (400, 401):
                    fallback_form = {
                        "grant_type": grant_type,
                        "scope": scope,
                        "client_id": client_id,
                    }
                    response2 = await client.post(
                        self.token_url,
                        data=fallback_form,
                        headers=headers,
                        auth=(client_id, client_secret),
                    )
                    print("MyInvois token attempt2 (basic) status:", response2.status_code)
                    if response2.status_code == 200:
                        data = response2.json()
                        expires_in = int(data.get("expires_in", 0))
                        self._access_token = data.get("access_token")
                        self._expires_at_epoch = time.time() + max(0, expires_in - 30)
                        return data

                    # Surface server message for easier debugging
                    try:
                        detail = response2.json()
                    except Exception:
                        detail = {"message": response2.text}
                    raise HTTPException(status_code=401, detail=detail)

                # Other errors
                logger.error(f"MyInvois token unexpected error {response.status_code}: {response.text}")
                try:
                    detail = response.json()
                except Exception:
                    detail = {"message": response.text}
                raise HTTPException(status_code=502, detail=detail)
        except httpx.TimeoutException:
            logger.error("MyInvois token request timeout")
            raise HTTPException(status_code=504, detail="MyInvois token request timeout")
        except httpx.RequestError as e:
            logger.error(f"MyInvois token request error: {str(e)}")
            raise HTTPException(status_code=502, detail="Failed to connect to MyInvois")

    async def get_valid_token(self) -> str:
        """Return a cached valid token, or fetch a new one if expired/missing."""
        if self._access_token and time.time() < self._expires_at_epoch:
            return self._access_token
        data = await self.fetch_token()
        return data["access_token"]

    async def get_document_by_id(self, document_id: str) -> Dict[str, Any]:
        token = await self.get_valid_token()
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        }
        url = f"{self.api_base}/documents/{document_id}"
        try:
            async with httpx.AsyncClient(timeout=settings.LHDN_API_TIMEOUT) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code == 404:
                    raise HTTPException(status_code=404, detail="Document not found")
                if resp.status_code == 401:
                    # Force refresh once if unauthorized
                    self._access_token = None
                    token = await self.get_valid_token()
                    headers["Authorization"] = f"Bearer {token}"
                    resp2 = await client.get(url, headers=headers)
                    if resp2.status_code == 200:
                        return resp2.json()
                    raise HTTPException(status_code=resp2.status_code, detail=resp2.text)
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="MyInvois request timeout")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail="Failed to connect to MyInvois")

    async def validate_taxpayer_tin(self, tin: str, id_type: str, id_value: str) -> Dict[str, Any]:
        token = await self.get_valid_token()
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        }
        url = f"{self.api_base}/taxpayer/validate/{tin}"
        params = {"idType": id_type, "idValue": id_value}
        try:
            async with httpx.AsyncClient(timeout=settings.LHDN_API_TIMEOUT) as client:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    # Empty 200 body means TIN is valid per upstream behavior
                    if not resp.content or not (resp.text or "").strip():
                        return {"valid": True, "message": "TIN validated", "empty": True}
                    try:
                        return resp.json()
                    except ValueError:
                        return {"valid": False, "message": "Unexpected non-JSON response", "raw": resp.text}
                if resp.status_code == 404:
                    return {"valid": False, "message": "Taxpayer not found"}
                if resp.status_code == 401:
                    self._access_token = None
                    new_token = await self.get_valid_token()
                    headers["Authorization"] = f"Bearer {new_token}"
                    resp2 = await client.get(url, headers=headers, params=params)
                    if resp2.status_code == 200:
                        if not resp2.content or not (resp2.text or "").strip():
                            return {"valid": True, "message": "TIN validated", "empty": True}
                        try:
                            return resp2.json()
                        except ValueError:
                            return {"valid": False, "message": "Unexpected non-JSON response", "raw": resp2.text}
                    raise HTTPException(status_code=resp2.status_code, detail=resp2.text)
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="MyInvois request timeout")
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Failed to connect to MyInvois")

    async def submit_document(self, document_payload: Dict[str, Any]) -> Dict[str, Any]:
        token = await self.get_valid_token()
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        url = f"{self.api_base}/documents/submit"
        try:
            async with httpx.AsyncClient(timeout=settings.LHDN_API_TIMEOUT) as client:
                resp = await client.post(url, headers=headers, json=document_payload)
                if resp.status_code in (200, 201):
                    try:
                        return resp.json()
                    except ValueError:
                        return {"message": "Submitted, non-JSON response", "raw": resp.text}
                if resp.status_code == 401:
                    self._access_token = None
                    new_token = await self.get_valid_token()
                    headers["Authorization"] = f"Bearer {new_token}"
                    resp2 = await client.post(url, headers=headers, json=document_payload)
                    if resp2.status_code in (200, 201):
                        return resp2.json()
                    raise HTTPException(status_code=resp2.status_code, detail=resp2.text)
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="MyInvois request timeout")
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Failed to connect to MyInvois")


myinvois_auth_service = MyInvoisAuthService()


