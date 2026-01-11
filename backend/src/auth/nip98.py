"""NIP-98 HTTP Auth implementation for Nostr-based authentication.

NIP-98 defines HTTP authentication using signed Nostr events.
The client creates a kind 27235 event with:
- 'u' tag: the absolute URL of the request
- 'method' tag: the HTTP method (GET, POST, etc.)
- 'payload' tag (optional): SHA256 hash of the request body

The event is base64 encoded and sent in the Authorization header.

This module verifies:
1. The event signature is valid
2. The event is recent (within expiry window)
3. The URL and method match the request
4. The pubkey is in the whitelist (if provided)

Reference: https://github.com/nostr-protocol/nips/blob/master/98.md
"""

import base64
import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Optional

from secp256k1 import PublicKey
from loguru import logger


# Event kind for NIP-98 HTTP Auth
NIP98_KIND = 27235

# Default expiry time (seconds) - events older than this are rejected
DEFAULT_EXPIRY_SECONDS = 60


@dataclass
class AuthResult:
    """Result of NIP-98 authentication."""
    
    valid: bool
    pubkey: Optional[str] = None  # hex pubkey if valid
    npub: Optional[str] = None  # npub if valid
    error: Optional[str] = None


def npub_to_hex(npub: str) -> Optional[str]:
    """Convert npub to hex pubkey.
    
    Args:
        npub: Nostr npub string (e.g., npub1...)
        
    Returns:
        32-byte hex pubkey or None if invalid
    """
    try:
        import bech32
        hrp, data = bech32.bech32_decode(npub)
        if hrp != "npub" or data is None:
            return None
        # Convert 5-bit groups back to 8-bit bytes
        decoded = bech32.convertbits(data, 5, 8, False)
        if decoded is None or len(decoded) != 32:
            return None
        return bytes(decoded).hex()
    except Exception:
        return None


def hex_to_npub(hex_pubkey: str) -> Optional[str]:
    """Convert hex pubkey to npub.
    
    Args:
        hex_pubkey: 32-byte hex pubkey
        
    Returns:
        npub string or None if invalid
    """
    try:
        import bech32
        pubkey_bytes = bytes.fromhex(hex_pubkey)
        if len(pubkey_bytes) != 32:
            return None
        # Convert 8-bit bytes to 5-bit groups
        data = bech32.convertbits(list(pubkey_bytes), 8, 5, True)
        if data is None:
            return None
        return bech32.bech32_encode("npub", data)
    except Exception:
        return None


def verify_event_signature(event: dict) -> bool:
    """Verify the Schnorr signature of a Nostr event.
    
    Args:
        event: Nostr event dict with id, pubkey, sig fields
        
    Returns:
        True if signature is valid
    """
    try:
        # Reconstruct the event ID (hash of serialized event)
        serialized = json.dumps([
            0,  # reserved
            event["pubkey"],
            event["created_at"],
            event["kind"],
            event["tags"],
            event["content"],
        ], separators=(',', ':'), ensure_ascii=False)
        
        event_hash = hashlib.sha256(serialized.encode()).hexdigest()
        
        # Verify ID matches
        if event_hash != event["id"]:
            logger.warning(f"[NIP-98] Event ID mismatch: expected {event_hash}, got {event['id']}")
            return False
        
        # Verify Schnorr signature
        pubkey_bytes = bytes.fromhex(event["pubkey"])
        sig_bytes = bytes.fromhex(event["sig"])
        msg_bytes = bytes.fromhex(event["id"])
        
        # Create x-only pubkey (prepend 0x02 for even y-coordinate)
        xonly_pubkey = PublicKey(b'\x02' + pubkey_bytes, raw=True)
        
        # Verify signature
        return xonly_pubkey.schnorr_verify(msg_bytes, sig_bytes, bip340tag=None, raw=True)
        
    except Exception as e:
        logger.error(f"[NIP-98] Signature verification error: {e}")
        return False


def get_tag_value(event: dict, tag_name: str) -> Optional[str]:
    """Get the first value of a tag from event.
    
    Args:
        event: Nostr event dict
        tag_name: Tag name to look for
        
    Returns:
        First tag value or None
    """
    for tag in event.get("tags", []):
        if len(tag) >= 2 and tag[0] == tag_name:
            return tag[1]
    return None


def verify_nip98_event(
    auth_header: str,
    url: str,
    method: str,
    body: Optional[bytes] = None,
    allowed_pubkeys: Optional[list[str]] = None,
    expiry_seconds: int = DEFAULT_EXPIRY_SECONDS,
) -> AuthResult:
    """Verify a NIP-98 authorization header.
    
    Args:
        auth_header: Authorization header value (Nostr <base64-event>)
        url: The absolute URL of the request
        method: HTTP method (GET, POST, etc.)
        body: Request body bytes (for payload hash verification)
        allowed_pubkeys: Optional list of allowed pubkeys (hex format)
        expiry_seconds: Maximum age of the event in seconds
        
    Returns:
        AuthResult with validation status
    """
    # Check header format
    if not auth_header.startswith("Nostr "):
        return AuthResult(valid=False, error="Invalid auth header format")
    
    # Extract and decode base64 event
    try:
        b64_event = auth_header[6:]  # Remove "Nostr " prefix
        # Handle URL-safe base64 and add padding if needed
        b64_event = b64_event.replace('-', '+').replace('_', '/')
        padding = 4 - len(b64_event) % 4
        if padding != 4:
            b64_event += '=' * padding
        event_json = base64.b64decode(b64_event).decode('utf-8')
        event = json.loads(event_json)
    except Exception as e:
        return AuthResult(valid=False, error=f"Failed to decode event: {e}")
    
    # Verify event kind
    if event.get("kind") != NIP98_KIND:
        return AuthResult(valid=False, error=f"Invalid event kind: {event.get('kind')}")
    
    # Verify event signature
    if not verify_event_signature(event):
        return AuthResult(valid=False, error="Invalid event signature")
    
    # Verify event is not expired
    created_at = event.get("created_at", 0)
    current_time = int(time.time())
    if current_time - created_at > expiry_seconds:
        return AuthResult(valid=False, error="Event expired")
    
    # Verify event is not from the future (with small tolerance)
    if created_at > current_time + 60:  # 1 minute tolerance
        return AuthResult(valid=False, error="Event from the future")
    
    # Verify URL tag
    event_url = get_tag_value(event, "u")
    if not event_url:
        return AuthResult(valid=False, error="Missing 'u' tag")
    
    # Normalize URLs for comparison (ignore trailing slashes)
    if event_url.rstrip('/') != url.rstrip('/'):
        return AuthResult(valid=False, error=f"URL mismatch: {event_url} != {url}")
    
    # Verify method tag
    event_method = get_tag_value(event, "method")
    if not event_method:
        return AuthResult(valid=False, error="Missing 'method' tag")
    
    if event_method.upper() != method.upper():
        return AuthResult(valid=False, error=f"Method mismatch: {event_method} != {method}")
    
    # Verify payload hash if body is present
    if body:
        expected_hash = hashlib.sha256(body).hexdigest()
        event_payload = get_tag_value(event, "payload")
        if event_payload and event_payload != expected_hash:
            return AuthResult(valid=False, error="Payload hash mismatch")
    
    # Get pubkey
    pubkey = event.get("pubkey")
    if not pubkey:
        return AuthResult(valid=False, error="Missing pubkey")
    
    # Verify pubkey is in whitelist if provided
    if allowed_pubkeys:
        # Normalize all pubkeys to hex
        normalized_allowed = []
        for pk in allowed_pubkeys:
            if pk.startswith("npub"):
                hex_pk = npub_to_hex(pk)
                if hex_pk:
                    normalized_allowed.append(hex_pk)
            else:
                normalized_allowed.append(pk)
        
        if pubkey not in normalized_allowed:
            return AuthResult(valid=False, error="Pubkey not authorized")
    
    # Convert pubkey to npub
    npub = hex_to_npub(pubkey)
    
    return AuthResult(
        valid=True,
        pubkey=pubkey,
        npub=npub,
    )


def get_admin_pubkeys() -> list[str]:
    """Get list of admin pubkeys from environment.
    
    The ADMIN_NPUBS environment variable should contain a comma-separated
    list of npub or hex pubkeys that are allowed admin access.
    
    Returns:
        List of pubkeys (may be npub or hex format)
    """
    admin_npubs = os.getenv("ADMIN_NPUBS", "")
    if not admin_npubs:
        return []
    return [pk.strip() for pk in admin_npubs.split(",") if pk.strip()]
