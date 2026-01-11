"""Admin API routes for wallet management.

These endpoints require NIP-98 authentication with a whitelisted admin npub.
They provide:
- Wallet statistics and balance
- Token generation for withdrawals
- Sweep all funds to a single token
- Manual Lightning payout
"""

from typing import Optional, List

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel, Field

from src.services.cashu import CashuService
from src.auth.nip98 import verify_nip98_event, get_admin_pubkeys, AuthResult

router = APIRouter()


class WithdrawRequest(BaseModel):
    """Request body for withdrawal."""
    amount: int = Field(..., gt=0, description="Amount in sats to withdraw")
    memo: Optional[str] = Field(None, description="Optional memo for the token")


class WithdrawResponse(BaseModel):
    """Response for withdrawal operation."""
    success: bool
    token: Optional[str] = None
    amount: int = 0
    error: Optional[str] = None


class SweepResponse(BaseModel):
    """Response for sweep operation."""
    success: bool
    token: Optional[str] = None
    amount: int = 0
    error: Optional[str] = None


class PayoutRequest(BaseModel):
    """Request body for Lightning payout."""
    amount: Optional[int] = Field(None, gt=0, description="Amount in sats (default: full balance)")
    ln_address: Optional[str] = Field(None, description="Lightning address (default: configured PAYOUT_LN_ADDRESS)")


class PayoutResponse(BaseModel):
    """Response for Lightning payout operation."""
    success: bool
    amount_sent: int = 0
    fee_paid: int = 0
    error: Optional[str] = None


class AdminStatsResponse(BaseModel):
    """Response for admin stats endpoint."""
    balance: int
    unit: str
    mint_url: str
    trusted_mints: List[str] = []
    keyset_count: int
    proof_count: int
    data_dir: str
    initialized: bool
    payout_enabled: bool = False
    payout_address: Optional[str] = None
    payout_threshold: int = 1000
    admin_pubkey: str  # The authenticated admin's pubkey


class AuthInfoResponse(BaseModel):
    """Response for auth info endpoint."""
    authenticated: bool
    pubkey: Optional[str] = None
    npub: Optional[str] = None
    is_admin: bool = False


def get_cashu_service(request: Request) -> CashuService:
    """Get the Cashu service from app state."""
    return request.app.state.cashu_service


async def verify_admin_auth(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> AuthResult:
    """Verify NIP-98 authentication for admin access.
    
    Args:
        request: FastAPI request object
        authorization: Authorization header
        
    Returns:
        AuthResult if valid
        
    Raises:
        HTTPException if authentication fails
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    # Get admin pubkeys from environment
    admin_pubkeys = get_admin_pubkeys()
    if not admin_pubkeys:
        raise HTTPException(
            status_code=503, 
            detail="No admin pubkeys configured. Set ADMIN_NPUBS environment variable."
        )
    
    # Build the full URL
    url = str(request.url)
    method = request.method
    
    # Get body for POST requests
    body = None
    if method in ("POST", "PUT", "PATCH"):
        body = await request.body()
    
    # Verify the NIP-98 event
    result = verify_nip98_event(
        auth_header=authorization,
        url=url,
        method=method,
        body=body,
        allowed_pubkeys=admin_pubkeys,
    )
    
    if not result.valid:
        raise HTTPException(status_code=401, detail=result.error or "Authentication failed")
    
    return result


@router.get("/auth/info", response_model=AuthInfoResponse)
async def get_auth_info(
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Check authentication status without requiring admin access.
    
    This endpoint can be used to verify NIP-98 authentication
    and check if the user is an admin.
    """
    if not authorization:
        return AuthInfoResponse(authenticated=False)
    
    admin_pubkeys = get_admin_pubkeys()
    url = str(request.url)
    method = request.method
    
    result = verify_nip98_event(
        auth_header=authorization,
        url=url,
        method=method,
        body=None,
        allowed_pubkeys=None,  # Allow any pubkey
    )
    
    if not result.valid:
        return AuthInfoResponse(authenticated=False)
    
    # Check if admin
    is_admin = False
    if admin_pubkeys and result.pubkey:
        from src.auth.nip98 import npub_to_hex
        normalized_admins = []
        for pk in admin_pubkeys:
            if pk.startswith("npub"):
                hex_pk = npub_to_hex(pk)
                if hex_pk:
                    normalized_admins.append(hex_pk)
            else:
                normalized_admins.append(pk)
        is_admin = result.pubkey in normalized_admins
    
    return AuthInfoResponse(
        authenticated=True,
        pubkey=result.pubkey,
        npub=result.npub,
        is_admin=is_admin,
    )


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Get detailed wallet statistics.
    
    Requires NIP-98 authentication with an admin pubkey.
    """
    auth = await verify_admin_auth(request, authorization)
    cashu_service = get_cashu_service(request)
    
    stats = cashu_service.get_stats()
    return AdminStatsResponse(
        **stats,
        admin_pubkey=auth.pubkey or "",
    )


@router.post("/withdraw", response_model=WithdrawResponse)
async def withdraw_funds(
    request: Request,
    body: WithdrawRequest,
    authorization: Optional[str] = Header(None),
):
    """Withdraw funds as an ecash token.
    
    Requires NIP-98 authentication with an admin pubkey.
    Generates an ecash token for the specified amount.
    """
    await verify_admin_auth(request, authorization)
    cashu_service = get_cashu_service(request)
    
    result = await cashu_service.generate_token(
        amount=body.amount,
        memo=body.memo or "PlebChat admin withdrawal",
    )
    
    if result.success:
        return WithdrawResponse(
            success=True,
            token=result.mint,  # Token is stored in mint field
            amount=result.amount,
        )
    else:
        return WithdrawResponse(
            success=False,
            error=result.error,
        )


@router.post("/sweep", response_model=SweepResponse)
async def sweep_all_funds(
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Sweep all funds into a single ecash token.
    
    Requires NIP-98 authentication with an admin pubkey.
    Generates an ecash token containing all available funds.
    """
    await verify_admin_auth(request, authorization)
    cashu_service = get_cashu_service(request)
    
    result = await cashu_service.sweep_all(memo="PlebChat wallet sweep")
    
    if result.success:
        return SweepResponse(
            success=True,
            token=result.mint,  # Token is stored in mint field
            amount=result.amount,
        )
    else:
        return SweepResponse(
            success=False,
            error=result.error,
        )


@router.post("/payout", response_model=PayoutResponse)
async def payout_to_lightning(
    request: Request,
    body: PayoutRequest,
    authorization: Optional[str] = Header(None),
):
    """Send funds to a Lightning address.
    
    Requires NIP-98 authentication with an admin pubkey.
    Uses the mint's melt capability to pay a Lightning invoice
    obtained from the Lightning address (LNURL-pay).
    
    If no amount is specified, sends the full balance.
    If no ln_address is specified, uses the configured PAYOUT_LN_ADDRESS.
    """
    await verify_admin_auth(request, authorization)
    cashu_service = get_cashu_service(request)
    
    result = await cashu_service.payout_to_lightning(
        amount=body.amount,
        ln_address=body.ln_address,
    )
    
    return PayoutResponse(
        success=result.success,
        amount_sent=result.amount_sent,
        fee_paid=result.fee_paid,
        error=result.error,
    )
