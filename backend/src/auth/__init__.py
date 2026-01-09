"""Authentication module for PlebChat backend."""

from .nip98 import (
    AuthResult,
    verify_nip98_event,
    get_admin_pubkeys,
    npub_to_hex,
    hex_to_npub,
)

__all__ = [
    "AuthResult",
    "verify_nip98_event",
    "get_admin_pubkeys",
    "npub_to_hex",
    "hex_to_npub",
]
