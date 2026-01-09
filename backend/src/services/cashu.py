"""Cashu ecash service for token redemption.

This service uses the official cashu (nutshell) library to:
- Parse tokens (cashuA/cashuB format)
- Redeem tokens using the library's built-in methods
- Manage wallet balance with persistent storage
- Generate tokens for withdrawal
- Automatic periodic withdrawals to Lightning address

Uses the wallet's deterministic BIP32 derivation as intended by the library.
The library handles SQLite table locking internally via lock_table="keysets"
in generate_n_secrets() to prevent counter race conditions.

An application-level asyncio.Lock provides defense-in-depth for serializing
redemption operations, with automatic recovery for "outputs already signed" errors.

Multi-mint support: Accepts tokens from any mint in TRUSTED_MINTS list.
"""

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cashu.core.helpers import sum_proofs
from cashu.core.settings import settings as cashu_settings
from cashu.wallet.helpers import deserialize_token_from_string
from cashu.wallet.wallet import Wallet
from loguru import logger

from .lnurl import (
    get_lnurl_pay_data,
    get_lnurl_invoice,
    estimate_lightning_fee,
    LNURLError,
)


@dataclass
class TokenResult:
    """Result of a token operation."""

    success: bool
    amount: int = 0
    error: Optional[str] = None
    mint: Optional[str] = None


@dataclass
class PayoutResult:
    """Result of a Lightning payout operation."""

    success: bool
    amount_sent: int = 0
    fee_paid: int = 0
    error: Optional[str] = None


class CashuServiceError(Exception):
    """Exception raised for CashuService configuration errors."""
    pass


# Default configuration
DEFAULT_MINT_URL = "https://mint.minibits.cash/Bitcoin"
DEFAULT_PAYOUT_THRESHOLD_SATS = 1000
DEFAULT_PAYOUT_INTERVAL_SECONDS = 300  # 5 minutes


class CashuService:
    """Cashu service for receiving and managing ecash tokens.
    
    Uses the nutshell library's built-in wallet methods which handle
    all cryptographic operations correctly with deterministic BIP32 derivation.
    
    REQUIRED Environment Variables:
    - WALLET_MNEMONIC: BIP39 mnemonic for the wallet
    
    OPTIONAL Environment Variables:
    - CASHU_MINT_URL: Primary mint URL (default: minibits)
    - TRUSTED_MINTS: Comma-separated list of trusted mint URLs
    - PAYOUT_LN_ADDRESS: Lightning address for automatic payouts
    - PAYOUT_THRESHOLD_SATS: Minimum balance to trigger payout (default: 1000)
    - PAYOUT_INTERVAL_SECONDS: Payout check interval (default: 300 = 5 min)
    """

    def __init__(self, data_dir: Optional[str] = None, require_mnemonic: bool = True):
        """Initialize CashuService.
        
        Args:
            data_dir: Path to data directory for wallet database
            require_mnemonic: If True, raises error if WALLET_MNEMONIC is not set
        """
        self._initialized = False
        self._wallet: Optional[Wallet] = None
        self._mnemonic = os.getenv("WALLET_MNEMONIC", "").strip()
        self._require_mnemonic = require_mnemonic
        
        # Mint configuration
        self._mint_url = os.getenv("CASHU_MINT_URL", DEFAULT_MINT_URL)
        
        # Trusted mints - parse comma-separated list, always include primary mint
        trusted_mints_env = os.getenv("TRUSTED_MINTS", "").strip()
        if trusted_mints_env:
            self._trusted_mints = {m.strip() for m in trusted_mints_env.split(",") if m.strip()}
        else:
            self._trusted_mints = set()
        # Always trust the primary mint
        self._trusted_mints.add(self._mint_url)
        
        # Payout configuration
        self._payout_ln_address = os.getenv("PAYOUT_LN_ADDRESS", "").strip()
        self._payout_threshold = int(os.getenv("PAYOUT_THRESHOLD_SATS", str(DEFAULT_PAYOUT_THRESHOLD_SATS)))
        self._payout_interval = int(os.getenv("PAYOUT_INTERVAL_SECONDS", str(DEFAULT_PAYOUT_INTERVAL_SECONDS)))
        
        # Background task handle
        self._payout_task: Optional[asyncio.Task] = None
        
        # Application-level mutex for serializing redemption operations.
        # The cashu library handles SQLite locking internally, but this provides
        # defense-in-depth and ensures clean error recovery.
        self._redemption_lock = asyncio.Lock()
        
        # Persistent storage directory
        if data_dir is None:
            self._data_dir = Path(__file__).parent.parent.parent / "data"
        else:
            self._data_dir = Path(data_dir)
        
        # Configure cashu settings
        cashu_settings.cashu_dir = str(self._data_dir)
        cashu_settings.tor = False
        cashu_settings.debug = False

    @staticmethod
    def validate_config() -> list[str]:
        """Validate required configuration.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        mnemonic = os.getenv("WALLET_MNEMONIC", "").strip()
        if not mnemonic:
            errors.append("WALLET_MNEMONIC environment variable is required")
        else:
            word_count = len(mnemonic.split())
            if word_count not in (12, 24):
                errors.append(f"WALLET_MNEMONIC should be 12 or 24 words, got {word_count}")
        
        # Validate payout configuration if set
        payout_addr = os.getenv("PAYOUT_LN_ADDRESS", "").strip()
        if payout_addr:
            if "@" not in payout_addr:
                errors.append("PAYOUT_LN_ADDRESS must be a valid Lightning address (user@domain.com)")
        
        return errors
    
    @property
    def trusted_mints(self) -> set[str]:
        """Get the set of trusted mint URLs."""
        return self._trusted_mints
    
    @property
    def payout_enabled(self) -> bool:
        """Check if automatic payout is enabled."""
        return bool(self._payout_ln_address)
    
    @property
    def payout_address(self) -> Optional[str]:
        """Get the configured payout Lightning address."""
        return self._payout_ln_address if self._payout_ln_address else None
    
    async def initialize(self):
        """Initialize the Cashu wallet with database persistence."""
        if self._require_mnemonic and not self._mnemonic:
            raise CashuServiceError(
                "WALLET_MNEMONIC environment variable is required. "
                "Generate one with: python -c \"from mnemonic import Mnemonic; print(Mnemonic('english').generate())\""
            )
        
        # Create data directory if it doesn't exist
        self._data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize wallet with database
        self._wallet = await Wallet.with_db(
            url=self._mint_url,
            db=str(self._data_dir),
            name="plebchat_wallet",
        )
        
        # Run database migrations
        await self._wallet._migrate_database()
        
        # Initialize private key with mnemonic if provided
        if self._mnemonic:
            await self._wallet._init_private_key(from_mnemonic=self._mnemonic)
            logger.info("[Cashu] Wallet initialized with provided mnemonic")
            # Security reminder for operators
            logger.warning(
                "[Cashu] IMPORTANT: Ensure WALLET_MNEMONIC is backed up securely! "
                "Losing the mnemonic means losing access to all funds."
            )
        else:
            await self._wallet._init_private_key()
            logger.warning("[Cashu] No mnemonic provided - wallet generated new one")
            logger.warning(
                "[Cashu] WARNING: Auto-generated mnemonic is NOT persisted! "
                "Funds will be LOST on restart. Set WALLET_MNEMONIC env var."
            )
        
        # Load mint keysets
        await self._wallet.load_mint()
        
        # Load existing proofs from database
        await self._wallet.load_proofs(reload=True)
        
        self._initialized = True
        logger.info(f"[Cashu] Wallet initialized with mint: {self._mint_url}")
        logger.info(f"[Cashu] Trusted mints: {', '.join(self._trusted_mints)}")
        logger.info(f"[Cashu] Data directory: {self._data_dir}")
        logger.info(f"[Cashu] Current balance: {self.balance} sats")
        logger.info(f"[Cashu] Loaded {len(self._wallet.proofs)} proofs")
        
        # Log payout configuration
        if self._payout_ln_address:
            logger.info(f"[Cashu] Automatic payout enabled to: {self._payout_ln_address}")
            logger.info(f"[Cashu] Payout threshold: {self._payout_threshold} sats")
            logger.info(f"[Cashu] Payout interval: {self._payout_interval} seconds")
        else:
            logger.info("[Cashu] Automatic payout disabled (set PAYOUT_LN_ADDRESS to enable)")
    
    async def start_payout_task(self):
        """Start the periodic payout background task."""
        if not self._payout_ln_address:
            logger.debug("[Cashu] Payout task not started - no PAYOUT_LN_ADDRESS configured")
            return
        
        if self._payout_task is not None:
            logger.warning("[Cashu] Payout task already running")
            return
        
        self._payout_task = asyncio.create_task(self._periodic_payout_loop())
        logger.info("[Cashu] Periodic payout task started")
    
    async def stop_payout_task(self):
        """Stop the periodic payout background task."""
        if self._payout_task is not None:
            self._payout_task.cancel()
            try:
                await self._payout_task
            except asyncio.CancelledError:
                pass
            self._payout_task = None
            logger.info("[Cashu] Periodic payout task stopped")
    
    async def _periodic_payout_loop(self):
        """Background task for periodic Lightning payouts."""
        logger.info(f"[Cashu] Starting payout loop (every {self._payout_interval}s, threshold {self._payout_threshold} sats)")
        
        while True:
            try:
                await asyncio.sleep(self._payout_interval)
                
                # Check if balance exceeds threshold
                current_balance = self.balance
                if current_balance >= self._payout_threshold:
                    logger.info(f"[Cashu] Balance {current_balance} sats >= threshold {self._payout_threshold}, initiating payout")
                    result = await self.payout_to_lightning(current_balance)
                    if result.success:
                        logger.info(f"[Cashu] Payout successful: {result.amount_sent} sats sent, {result.fee_paid} sats fee")
                    else:
                        logger.error(f"[Cashu] Payout failed: {result.error}")
                else:
                    logger.debug(f"[Cashu] Balance {current_balance} sats < threshold {self._payout_threshold}, skipping payout")
                    
            except asyncio.CancelledError:
                logger.info("[Cashu] Payout loop cancelled")
                break
            except Exception as e:
                logger.error(f"[Cashu] Error in payout loop: {e}")
                # Continue the loop after error
    
    @property
    def balance(self) -> int:
        """Get current wallet balance in sats."""
        if not self._wallet:
            return 0
        bal = self._wallet.available_balance
        # Handle Amount object from cashu library
        if hasattr(bal, 'amount'):
            return bal.amount
        return int(bal)

    def validate_token_format(self, token: str, check_mint: bool = True) -> tuple[bool, Optional[str]]:
        """Validate that a string is a valid Cashu token.
        
        Args:
            token: The cashu token string
            check_mint: If True, also validates the token is from a trusted mint
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not token:
            return False, "Empty token"
        
        if not token.startswith("cashuA") and not token.startswith("cashuB"):
            return False, "Invalid token format (must start with cashuA or cashuB)"
        
        try:
            parsed = deserialize_token_from_string(token)
            if not parsed.proofs:
                return False, "Token contains no proofs"
            
            # Check if token is from a trusted mint
            if check_mint and parsed.mint:
                if parsed.mint not in self._trusted_mints:
                    return False, f"Token from untrusted mint: {parsed.mint}. Trusted mints: {', '.join(self._trusted_mints)}"
            
            return True, None
        except Exception as e:
            return False, f"Failed to parse token: {str(e)}"
    
    def is_trusted_mint(self, mint_url: str) -> bool:
        """Check if a mint URL is trusted.
        
        Args:
            mint_url: The mint URL to check
            
        Returns:
            True if the mint is trusted
        """
        return mint_url in self._trusted_mints

    def get_token_amount(self, token: str) -> tuple[int, Optional[str]]:
        """Get the amount contained in a token without redeeming it.
        
        Args:
            token: The cashu token string (cashuA... or cashuB...)
            
        Returns:
            Tuple of (amount in sats, error message if any)
        """
        if not token:
            return 0, "Empty token"
        
        try:
            parsed = deserialize_token_from_string(token)
            if not parsed.proofs:
                return 0, "Token contains no proofs"
            return sum_proofs(parsed.proofs), None
        except Exception as e:
            return 0, f"Failed to parse token: {str(e)}"

    async def receive_token(self, token: str) -> TokenResult:
        """Receive and redeem an ecash token.
        
        Uses the wallet's built-in redeem() method which handles all
        cryptographic operations correctly with deterministic secrets.
        
        Serializes redemptions via asyncio.Lock for defense-in-depth.
        If "outputs already signed" error occurs, attempts recovery via
        the library's restore mechanism.
        
        Args:
            token: The cashu token string (cashuA... or cashuB...)
            
        Returns:
            TokenResult with success status and amount
        """
        if not self._initialized or not self._wallet:
            return TokenResult(success=False, error="Service not initialized")
        
        # Validate token format
        is_valid, error = self.validate_token_format(token)
        if not is_valid:
            return TokenResult(success=False, error=error)
        
        # Serialize redemption operations for defense-in-depth
        async with self._redemption_lock:
            return await self._redeem_token_internal(token)
    
    async def _redeem_token_internal(self, token: str, is_retry: bool = False) -> TokenResult:
        """Internal token redemption logic with retry support.
        
        Args:
            token: The cashu token string
            is_retry: Whether this is a retry after recovery
            
        Returns:
            TokenResult with success status and amount
        """
        try:
            # Parse the token using the library's helper
            parsed_token = deserialize_token_from_string(token)
            proofs = parsed_token.proofs
            token_amount = sum_proofs(proofs)
            token_mint = parsed_token.mint
            
            logger.info(f"[Cashu] Receiving token: {token_amount} sats from mint {token_mint}")
            
            # Ensure we have keysets for these proofs
            keyset_ids = list({p.id for p in proofs})
            for keyset_id in keyset_ids:
                if keyset_id not in self._wallet.keysets:
                    logger.debug(f"[Cashu] Loading keyset: {keyset_id}")
                    await self._wallet.load_mint_keysets()
            
            # Use the wallet's native redeem method
            # The library handles counter management and SQLite locking internally
            keep_proofs, _ = await self._wallet.redeem(proofs)
            redeemed_amount = sum_proofs(keep_proofs)
            
            # Reload proofs to update balance
            await self._wallet.load_proofs(reload=True)
            
            logger.info(f"[Cashu] Successfully redeemed {redeemed_amount} sats")
            logger.info(f"[Cashu] New wallet balance: {self.balance} sats")
            
            return TokenResult(
                success=True,
                amount=redeemed_amount,
                mint=token_mint or self._mint_url,
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[Cashu] Redemption failed: {error_msg}")
            
            # Handle "outputs already signed" error with recovery
            if "outputs have already been signed" in error_msg.lower() or "already signed" in error_msg.lower():
                if not is_retry:
                    logger.warning("[Cashu] Outputs already signed - attempting counter recovery")
                    recovery_success = await self._attempt_counter_recovery()
                    if recovery_success:
                        logger.info("[Cashu] Counter recovery succeeded, retrying redemption")
                        return await self._redeem_token_internal(token, is_retry=True)
                    else:
                        logger.error("[Cashu] Counter recovery failed")
                else:
                    logger.error("[Cashu] Retry after recovery still failed")
                
                # Log token for manual recovery
                logger.error(f"[Cashu] UNREDEEMED TOKEN FOR MANUAL RECOVERY: {token}")
                return TokenResult(
                    success=False, 
                    error="Counter sync error - please try again or contact support"
                )
            
            if "already spent" in error_msg.lower() or "spent" in error_msg.lower():
                return TokenResult(success=False, error="Token already spent")
            elif "invalid" in error_msg.lower():
                return TokenResult(success=False, error="Invalid token or proofs")
            
            return TokenResult(success=False, error=f"Redemption failed: {error_msg}")
    
    async def _attempt_counter_recovery(self) -> bool:
        """Attempt to recover counter state using the library's restore mechanism.
        
        This queries the mint to find the next unused counter position,
        recovering from any "burned" positions due to failed transactions.
        
        Returns:
            True if recovery succeeded, False otherwise
        """
        if not self._wallet:
            return False
        
        try:
            active_keyset = self._wallet.keyset_id if hasattr(self._wallet, 'keyset_id') else None
            if not active_keyset:
                logger.warning("[Cashu] No active keyset for recovery")
                return False
            
            logger.info(f"[Cashu] Running restore for keyset {active_keyset}")
            
            # Use the library's restore mechanism to resync counter with mint
            # This finds the highest counter position the mint has seen and sets
            # our local counter to match, recovering from any burned positions
            await self._wallet.restore_tokens_for_keyset(
                keyset_id=active_keyset,
                to=2,  # Stop after 2 consecutive empty batches
                batch=25,  # Check 25 positions per batch
            )
            
            logger.info("[Cashu] Counter recovery completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"[Cashu] Counter recovery failed: {e}")
            return False

    async def generate_token(self, amount: int, memo: Optional[str] = None) -> TokenResult:
        """Generate an ecash token for withdrawal.
        
        Args:
            amount: Amount in sats to include in the token
            memo: Optional memo for the token
            
        Returns:
            TokenResult with the token string in the 'mint' field
        """
        if not self._initialized or not self._wallet:
            return TokenResult(success=False, error="Service not initialized")
        
        if amount <= 0:
            return TokenResult(success=False, error="Amount must be positive")
        
        if amount > self.balance:
            return TokenResult(success=False, error=f"Insufficient balance: {self.balance} sats")
        
        try:
            # Reload proofs to ensure we have the latest
            await self._wallet.load_proofs(reload=True)
            await self._wallet.load_mint()
            
            # Select proofs to send
            send_proofs, fees = await self._wallet.select_to_send(
                self._wallet.proofs,
                amount,
                set_reserved=False,
                offline=False,
                include_fees=False,
            )
            
            # Serialize proofs to token (V4 format)
            token_str = await self._wallet.serialize_proofs(
                send_proofs,
                include_dleq=True,
                legacy=False,
                memo=memo,
            )
            
            # Mark proofs as reserved
            await self._wallet.set_reserved_for_send(send_proofs, reserved=True)
            
            logger.info(f"[Cashu] Generated token for {sum_proofs(send_proofs)} sats")
            
            return TokenResult(
                success=True,
                amount=sum_proofs(send_proofs),
                mint=token_str,
            )
            
        except Exception as e:
            logger.error(f"[Cashu] Token generation failed: {e}")
            return TokenResult(success=False, error=str(e))
    
    async def check_token_spent(self, token: str) -> bool:
        """Check if a token has already been spent."""
        if not self._initialized or not self._wallet:
            return True
        
        try:
            parsed = deserialize_token_from_string(token)
            proof_states = await self._wallet.check_proof_state(parsed.proofs)
            return any(state.spent for state in proof_states.states)
        except Exception as e:
            logger.error(f"[Cashu] Error checking token state: {e}")
            return True
    
    def get_stats(self) -> dict:
        """Get wallet statistics."""
        if not self._wallet:
            return {
                "balance": 0,
                "unit": "sat",
                "mint_url": self._mint_url,
                "keyset_count": 0,
                "proof_count": 0,
                "data_dir": str(self._data_dir),
                "initialized": False,
            }
        
        return {
            "balance": self.balance,
            "unit": str(self._wallet.unit.name) if hasattr(self._wallet.unit, 'name') else "sat",
            "mint_url": self._mint_url,
            "keyset_count": len(self._wallet.keysets),
            "proof_count": len(self._wallet.proofs),
            "data_dir": str(self._data_dir),
            "initialized": self._initialized,
        }

    async def sweep_all(self, memo: Optional[str] = None) -> TokenResult:
        """Sweep all funds into a single token."""
        if not self._initialized or not self._wallet:
            return TokenResult(success=False, error="Service not initialized")
        
        current_balance = self.balance
        if current_balance <= 0:
            return TokenResult(success=False, error="No funds to sweep")
        
        return await self.generate_token(current_balance, memo=memo or "PlebChat wallet sweep")
    
    async def payout_to_lightning(
        self, 
        amount: Optional[int] = None,
        ln_address: Optional[str] = None
    ) -> PayoutResult:
        """Send funds to a Lightning address via the mint.
        
        Uses the mint's melt capability to pay a Lightning invoice
        obtained from the Lightning address (LNURL-pay).
        
        Args:
            amount: Amount in sats to send (default: full balance)
            ln_address: Lightning address to pay (default: configured PAYOUT_LN_ADDRESS)
            
        Returns:
            PayoutResult with success status and amounts
        """
        if not self._initialized or not self._wallet:
            return PayoutResult(success=False, error="Service not initialized")
        
        # Use configured address if not provided
        target_address = ln_address or self._payout_ln_address
        if not target_address:
            return PayoutResult(success=False, error="No Lightning address configured")
        
        # Use full balance if amount not specified
        current_balance = self.balance
        payout_amount = amount if amount is not None else current_balance
        
        if payout_amount <= 0:
            return PayoutResult(success=False, error="No funds to payout")
        
        if payout_amount > current_balance:
            return PayoutResult(success=False, error=f"Insufficient balance: {current_balance} sats")
        
        # Estimate fee and ensure we can afford it
        estimated_fee = estimate_lightning_fee(payout_amount)
        if payout_amount <= estimated_fee:
            return PayoutResult(success=False, error=f"Amount too small to cover estimated fee ({estimated_fee} sats)")
        
        # Amount to request from LNURL (after fee estimation)
        net_amount = payout_amount - estimated_fee
        
        async with self._redemption_lock:
            return await self._payout_internal(target_address, payout_amount, net_amount)
    
    async def _payout_internal(
        self, 
        ln_address: str, 
        total_amount: int,
        net_amount: int
    ) -> PayoutResult:
        """Internal payout logic.
        
        Args:
            ln_address: Lightning address to pay
            total_amount: Total amount of proofs to use
            net_amount: Amount to request in invoice (after fee reserve)
            
        Returns:
            PayoutResult with success status and amounts
        """
        try:
            # 1. Get LNURL-pay data from Lightning address
            logger.info(f"[Cashu] Getting LNURL-pay data from {ln_address}")
            try:
                pay_data = await get_lnurl_pay_data(ln_address)
            except LNURLError as e:
                return PayoutResult(success=False, error=f"LNURL error: {e}")
            
            # 2. Validate amount is within LNURL limits
            net_amount_msat = net_amount * 1000
            if net_amount_msat < pay_data["min_sendable"]:
                return PayoutResult(
                    success=False, 
                    error=f"Amount {net_amount} sats below minimum {pay_data['min_sendable'] // 1000} sats"
                )
            if net_amount_msat > pay_data["max_sendable"]:
                return PayoutResult(
                    success=False, 
                    error=f"Amount {net_amount} sats above maximum {pay_data['max_sendable'] // 1000} sats"
                )
            
            # 3. Request Lightning invoice from LNURL callback
            logger.info(f"[Cashu] Requesting invoice for {net_amount} sats")
            try:
                bolt11_invoice = await get_lnurl_invoice(pay_data["callback_url"], net_amount_msat)
            except LNURLError as e:
                return PayoutResult(success=False, error=f"Failed to get invoice: {e}")
            
            # 4. Get melt quote from mint
            logger.info("[Cashu] Getting melt quote from mint")
            melt_quote = await self._wallet.melt_quote(bolt11_invoice)
            
            # 5. Select proofs to pay (including fee reserve)
            # Total needed = invoice amount + fee reserve
            total_needed = melt_quote.amount + melt_quote.fee_reserve
            
            await self._wallet.load_proofs(reload=True)
            
            if total_needed > self.balance:
                return PayoutResult(
                    success=False, 
                    error=f"Insufficient balance for payment + fees: need {total_needed}, have {self.balance}"
                )
            
            # Select proofs for the payment
            send_proofs, _ = await self._wallet.select_to_send(
                self._wallet.proofs,
                total_needed,
                set_reserved=True,
                offline=False,
                include_fees=True,
            )
            
            # 6. Execute melt (pay the Lightning invoice)
            logger.info(f"[Cashu] Melting {sum_proofs(send_proofs)} sats to pay invoice")
            melt_response = await self._wallet.melt(
                proofs=send_proofs,
                invoice=bolt11_invoice,
                fee_reserve_sat=melt_quote.fee_reserve,
                quote_id=melt_quote.quote,
            )
            
            # 7. Reload proofs to update balance
            await self._wallet.load_proofs(reload=True)
            
            # Calculate actual fee paid
            actual_fee = sum_proofs(send_proofs) - net_amount
            
            logger.info(f"[Cashu] Payout complete: {net_amount} sats sent, {actual_fee} sats fee")
            logger.info(f"[Cashu] New wallet balance: {self.balance} sats")
            
            return PayoutResult(
                success=True,
                amount_sent=net_amount,
                fee_paid=actual_fee,
            )
            
        except Exception as e:
            logger.error(f"[Cashu] Payout failed: {e}")
            return PayoutResult(success=False, error=str(e))