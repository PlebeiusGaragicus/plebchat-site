"""Wallet API routes for ecash token operations.

These endpoints are called by the LangGraph agent to:
- Validate tokens before processing
- Redeem tokens on successful completion
"""

from typing import Optional

from fastapi import APIRouter, Request
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
    error: Optional[str] = None
    mint: Optional[str] = None


class CheckTokenRequest(BaseModel):
    """Request body for checking token state."""
    token: str = Field(..., description="The cashu ecash token to check")


class CheckTokenResponse(BaseModel):
    """Response for token check operation."""
    valid: bool
    spent: bool = False
    amount: int = 0
    error: Optional[str] = None


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
    """Check if a token is valid, unspent, and return its amount.
    
    This endpoint can be used to validate a token before processing.
    It checks the token format, queries the mint for spend state,
    and returns the token amount for pricing validation.
    
    Returns:
        Token validity, spend state, and amount in sats
    """
    cashu_service = get_cashu_service(request)
    
    # Validate format and get amount
    is_valid, error = cashu_service.validate_token_format(body.token)
    
    if not is_valid:
        return CheckTokenResponse(valid=False, error=error)
    
    # Get token amount
    token_amount, amount_error = cashu_service.get_token_amount(body.token)
    if amount_error:
        return CheckTokenResponse(valid=False, error=amount_error)
    
    # Check if spent
    is_spent = await cashu_service.check_token_spent(body.token)
    
    return CheckTokenResponse(
        valid=True,
        spent=is_spent,
        amount=token_amount,
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


class StatsResponse(BaseModel):
    """Response for wallet statistics."""
    balance: int
    unit: str = "sat"
    mint_url: str
    keyset_count: int = 0
    proof_count: int = 0
    data_dir: str = ""
    initialized: bool = False


@router.get("/stats", response_model=StatsResponse)
async def get_stats(request: Request):
    """Get wallet statistics.
    
    This endpoint is useful for debugging and verifying
    the wallet state.
    
    Returns:
        Wallet statistics
    """
    cashu_service = get_cashu_service(request)
    stats = cashu_service.get_stats()
    
    return StatsResponse(**stats)
