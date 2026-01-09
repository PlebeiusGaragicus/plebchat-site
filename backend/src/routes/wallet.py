"""Wallet API routes for ecash token operations.

These endpoints are called by the LangGraph agent to:
- Validate tokens before processing
- Redeem tokens on successful completion
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.services.cashu import CashuService, TokenResult

router = APIRouter()


class ReceiveTokenRequest(BaseModel):
    """Request body for receiving an ecash token."""
    token: str = Field(..., description="The cashu ecash token to receive")


class ReceiveTokenResponse(BaseModel):
    """Response for token receive operation."""
    success: bool
    amount: int = 0
    error: str | None = None
    mint: str | None = None


class CheckTokenRequest(BaseModel):
    """Request body for checking token state."""
    token: str = Field(..., description="The cashu ecash token to check")


class CheckTokenResponse(BaseModel):
    """Response for token check operation."""
    valid: bool
    spent: bool = False
    error: str | None = None


class BalanceResponse(BaseModel):
    """Response for balance query."""
    balance: int
    unit: str = "sat"


def get_cashu_service(request: Request) -> CashuService:
    """Get the Cashu service from app state."""
    return request.app.state.cashu_service


@router.post("/receive", response_model=ReceiveTokenResponse)
async def receive_token(request: Request, body: ReceiveTokenRequest):
    """Receive and redeem an ecash token.
    
    This endpoint is called by the LangGraph agent after successfully
    processing a request. The token is validated and added to the
    backend wallet.
    
    Returns:
        Token result with amount received
    """
    cashu_service = get_cashu_service(request)
    
    print(f"[Wallet] Receiving token: {body.token[:20]}...")
    result = await cashu_service.receive_token(body.token)
    
    if result.success:
        print(f"[Wallet] Token received successfully: {result.amount} sats")
    else:
        print(f"[Wallet] Token receive failed: {result.error}")
    
    return ReceiveTokenResponse(
        success=result.success,
        amount=result.amount,
        error=result.error,
        mint=result.mint,
    )


@router.post("/check", response_model=CheckTokenResponse)
async def check_token(request: Request, body: CheckTokenRequest):
    """Check if a token is valid and unspent.
    
    This endpoint can be used to validate a token before processing.
    It checks the token format and queries the mint for spend state.
    
    Returns:
        Token validity and spend state
    """
    cashu_service = get_cashu_service(request)
    
    # Validate format
    is_valid, error = cashu_service.validate_token_format(body.token)
    
    if not is_valid:
        return CheckTokenResponse(valid=False, error=error)
    
    # Check if spent
    is_spent = await cashu_service.check_token_spent(body.token)
    
    return CheckTokenResponse(
        valid=True,
        spent=is_spent,
        error=None,
    )


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(request: Request):
    """Get the current wallet balance.
    
    Returns the total sats received by this backend wallet.
    
    Returns:
        Current balance in sats
    """
    cashu_service = get_cashu_service(request)
    
    return BalanceResponse(
        balance=cashu_service.balance,
        unit="sat",
    )
