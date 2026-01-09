"""LNURL utilities for Lightning address payments.

This module provides LNURL-pay functionality for automatic withdrawals
to Lightning addresses (user@domain.com format).

Reference: https://github.com/lnurl/luds
"""

import math
from typing import TypedDict

import httpx
from loguru import logger

try:
    from bech32 import bech32_decode, convertbits
except ModuleNotFoundError:
    bech32_decode = None  # type: ignore
    convertbits = None  # type: ignore


class LNURLPayData(TypedDict):
    """LNURL payRequest response data."""
    callback_url: str
    min_sendable: int  # millisatoshi
    max_sendable: int  # millisatoshi


class LNURLError(Exception):
    """LNURL operation error."""
    pass


async def decode_lnurl(lnurl: str) -> str:
    """Decode LNURL to get the actual URL.
    
    Handles:
    - lightning: prefix
    - user@host format (Lightning Address)
    - bech32 encoded lnurl
    - direct HTTPS URLs
    
    Args:
        lnurl: LNURL string in any supported format
        
    Returns:
        The decoded HTTPS URL
        
    Raises:
        LNURLError: If the LNURL format is invalid
    """
    # Remove lightning: prefix if present
    if lnurl.startswith("lightning:"):
        lnurl = lnurl[10:]
    
    # Handle user@host format (Lightning Address)
    if "@" in lnurl and len(lnurl.split("@")) == 2:
        user, host = lnurl.split("@")
        return f"https://{host}/.well-known/lnurlp/{user}"
    
    # Handle bech32 encoded LNURL
    if lnurl.lower().startswith("lnurl"):
        if bech32_decode is None or convertbits is None:
            raise LNURLError(
                "bech32 library is required for LNURL bech32 decoding"
            )
        
        try:
            hrp, data = bech32_decode(lnurl)
            if data is None:
                raise LNURLError("Invalid bech32 data in LNURL")
            
            decoded_data = convertbits(data, 5, 8, False)
            if decoded_data is None:
                raise LNURLError("Failed to convert LNURL bits")
            
            return bytes(decoded_data).decode("utf-8")
        except Exception as e:
            raise LNURLError(f"Failed to decode LNURL: {e}") from e
    
    # Assume it's a direct URL
    if not lnurl.startswith("https://"):
        raise LNURLError("Direct LNURL must use HTTPS")
    
    return lnurl


async def get_lnurl_pay_data(lnurl: str, timeout: float = 10.0) -> LNURLPayData:
    """Fetch LNURL payRequest data.
    
    Args:
        lnurl: LNURL string in any supported format
        timeout: HTTP request timeout in seconds
        
    Returns:
        LNURLPayData with callback URL and sendable amounts
        
    Raises:
        LNURLError: If the LNURL data is invalid
    """
    url = await decode_lnurl(lnurl)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, follow_redirects=True, timeout=timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise LNURLError(f"HTTP error fetching LNURL data: {e}") from e
    
    lnurl_data = response.json()
    
    # Validate payRequest data
    if lnurl_data.get("tag") != "payRequest":
        raise LNURLError(
            f"Invalid LNURL tag: expected 'payRequest', got '{lnurl_data.get('tag')}'"
        )
    
    if not isinstance(lnurl_data.get("callback"), str):
        raise LNURLError("Invalid LNURL payRequest: missing callback URL")
    
    return LNURLPayData(
        callback_url=lnurl_data["callback"],
        min_sendable=lnurl_data.get("minSendable", 1000),  # Default 1 sat
        max_sendable=lnurl_data.get("maxSendable", 1_000_000_000_000),  # Default 1M sats
    )


async def get_lnurl_invoice(
    callback_url: str, 
    amount_msat: int,
    timeout: float = 10.0
) -> str:
    """Request a Lightning invoice from LNURL callback.
    
    Args:
        callback_url: The LNURL callback URL
        amount_msat: Amount in millisatoshi
        timeout: HTTP request timeout in seconds
        
    Returns:
        BOLT11 invoice string
        
    Raises:
        LNURLError: If the response is invalid
    """
    # Add amount parameter (some callbacks use ? some use &)
    separator = "&" if "?" in callback_url else "?"
    request_url = f"{callback_url}{separator}amount={amount_msat}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(request_url, follow_redirects=True, timeout=timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise LNURLError(f"HTTP error requesting invoice: {e}") from e
    
    invoice_data = response.json()
    
    if "pr" not in invoice_data:
        # Check if there's an error in the response
        if "reason" in invoice_data:
            raise LNURLError(f"LNURL error: {invoice_data['reason']}")
        raise LNURLError(f"Invalid LNURL invoice response: {invoice_data}")
    
    return invoice_data["pr"]


async def validate_lightning_address(address: str) -> bool:
    """Validate that a Lightning address is reachable and valid.
    
    Args:
        address: Lightning address (user@domain.com format)
        
    Returns:
        True if valid and reachable
    """
    try:
        if "@" not in address or len(address.split("@")) != 2:
            return False
        
        pay_data = await get_lnurl_pay_data(address, timeout=5.0)
        return pay_data["min_sendable"] > 0
    except Exception as e:
        logger.debug(f"[LNURL] Address validation failed for {address}: {e}")
        return False


def estimate_lightning_fee(amount_sats: int, fee_ppm: int = 10000) -> int:
    """Estimate Lightning routing fee.
    
    Args:
        amount_sats: Amount to send in satoshis
        fee_ppm: Fee in parts per million (default 1% = 10000 ppm)
        
    Returns:
        Estimated fee in satoshis (minimum 2 sats)
    """
    fee = math.ceil(amount_sats * fee_ppm / 1_000_000)
    return max(fee, 2)
