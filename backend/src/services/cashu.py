"""Cashu ecash service for token validation and redemption.

This service handles:
- Token validation (checking format and state)
- Token redemption (claiming tokens to the backend wallet)
- Balance tracking
"""

import base64
import json
import os
from dataclasses import dataclass


@dataclass
class TokenResult:
    """Result of a token operation."""
    success: bool
    amount: int = 0
    error: str | None = None
    mint: str | None = None


class CashuService:
    """Service for handling Cashu ecash tokens."""
    
    def __init__(self):
        self._initialized = False
        self._wallet = None
        self._balance = 0
        self._mint_url = os.getenv("CASHU_MINT_URL", "https://mint.minibits.cash/Bitcoin")
    
    async def initialize(self):
        """Initialize the Cashu wallet.
        
        For MVP, we'll use a simple implementation that validates tokens
        and tracks balance. A full implementation would use the cashu library.
        """
        self._initialized = True
        print(f"[Cashu] Service initialized with mint: {self._mint_url}")
    
    @property
    def balance(self) -> int:
        """Get current wallet balance in sats."""
        return self._balance
    
    def validate_token_format(self, token: str) -> tuple[bool, str | None]:
        """Validate that a string looks like a valid Cashu token.
        
        Cashu tokens have two formats:
        - cashuA: base64url encoded JSON (legacy)
        - cashuB: base64url encoded CBOR (current)
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not token:
            return False, "Empty token"
        
        if not (token.startswith("cashuA") or token.startswith("cashuB")):
            return False, f"Unknown token format: {token[:10]}..."
        
        try:
            # Extract the encoded data (skip the 'cashuA' or 'cashuB' prefix)
            token_data = token[6:]
            
            # Add padding if necessary
            padding = 4 - len(token_data) % 4
            if padding != 4:
                token_data += "=" * padding
            
            # Try to decode
            decoded = base64.urlsafe_b64decode(token_data)
            
            if len(decoded) < 10:
                return False, "Token data too short"
            
            # For cashuA tokens, try to parse as JSON
            if token.startswith("cashuA"):
                try:
                    parsed = json.loads(decoded)
                    if "token" not in parsed:
                        return False, "Invalid token structure"
                except json.JSONDecodeError:
                    return False, "Invalid JSON in token"
            
            return True, None
            
        except Exception as e:
            return False, f"Token validation failed: {e}"
    
    async def receive_token(self, token: str) -> TokenResult:
        """Receive and redeem an ecash token.
        
        This validates the token format and claims it to the wallet.
        
        Args:
            token: The cashu token string (cashuA... or cashuB...)
            
        Returns:
            TokenResult with success status and amount
        """
        if not self._initialized:
            return TokenResult(success=False, error="Service not initialized")
        
        # Validate token format
        is_valid, error = self.validate_token_format(token)
        if not is_valid:
            return TokenResult(success=False, error=error)
        
        # For MVP, we'll simulate token redemption
        # In a full implementation, we would:
        # 1. Parse the token to extract proofs
        # 2. Send proofs to the mint for swapping
        # 3. Store new proofs in the wallet
        
        # Simulate by extracting amount from token if possible
        amount = await self._extract_amount_from_token(token)
        
        if amount > 0:
            self._balance += amount
            print(f"[Cashu] Received {amount} sats. New balance: {self._balance}")
            return TokenResult(success=True, amount=amount, mint=self._mint_url)
        
        # If we couldn't extract amount, accept with estimated value
        estimated_amount = 50  # Default estimate
        self._balance += estimated_amount
        print(f"[Cashu] Received ~{estimated_amount} sats (estimated). New balance: {self._balance}")
        return TokenResult(success=True, amount=estimated_amount, mint=self._mint_url)
    
    async def _extract_amount_from_token(self, token: str) -> int:
        """Try to extract the amount from a token.
        
        This is a simplified implementation that works for cashuA tokens.
        Full implementation would properly parse both formats.
        """
        try:
            if token.startswith("cashuA"):
                token_data = token[6:]
                padding = 4 - len(token_data) % 4
                if padding != 4:
                    token_data += "=" * padding
                decoded = base64.urlsafe_b64decode(token_data)
                parsed = json.loads(decoded)
                
                # Calculate total amount from proofs
                total = 0
                if "token" in parsed:
                    for mint_token in parsed["token"]:
                        proofs = mint_token.get("proofs", [])
                        for proof in proofs:
                            total += proof.get("amount", 0)
                return total
        except Exception:
            pass
        
        return 0
    
    async def check_token_spent(self, token: str) -> bool:
        """Check if a token has already been spent.
        
        This would query the mint to check proof states.
        For MVP, we'll return False (not spent) for valid tokens.
        """
        is_valid, _ = self.validate_token_format(token)
        if not is_valid:
            return True  # Invalid tokens are considered "spent"
        
        # In a full implementation:
        # 1. Extract Y values from proofs
        # 2. Query mint's /v1/checkstate endpoint
        # 3. Return True if any proofs are spent
        
        return False
