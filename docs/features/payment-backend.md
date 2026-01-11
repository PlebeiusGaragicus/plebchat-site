# Payment Backend

The PlebChat backend is a FastAPI service that handles ecash payment validation, redemption, and wallet management. It serves as the payment infrastructure for the LangGraph AI agents.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend UI   │     │  LangGraph      │     │  Admin Panel    │
│   (Svelte)      │     │  Agent          │     │  (Svelte)       │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │  ecash token          │  /check, /receive     │  NIP-98 Auth
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  /api/wallet/*  │  │  /api/admin/*   │  │  CashuService   │  │
│  │  Token ops      │  │  NIP-98 auth    │  │  Wallet mgmt    │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │           │
│           └────────────────────┴────────────────────┘           │
│                                │                                 │
│                    ┌───────────┴───────────┐                    │
│                    │   SQLite Database     │                    │
│                    │   (proofs, keysets)   │                    │
│                    └───────────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌───────────────────────┐
                    │     Cashu Mint        │
                    │  (minibits default)   │
                    └───────────────────────┘
```

## Payment Flow

The payment flow follows a "redeem-first" pattern to prevent unpaid LLM usage:

```
1. Client sends message + ecash token to LangGraph Agent
2. Agent calls POST /api/wallet/check
   - Backend validates token format (cashuA/cashuB)
   - Backend checks token is unspent with the mint
   - Backend returns token amount for pricing validation
3. Agent verifies amount meets pricing requirements
4. Agent calls POST /api/wallet/receive (BEFORE LLM call)
   - Backend redeems token to its wallet immediately
   - Proofs are stored in SQLite database
   - If redemption fails: STOP, return token for client refund
5. Agent processes the LLM request (only after payment confirmed)
6. On LLM FAILURE: Payment is NOT refunded
   - We've already done the work of receiving the payment
```

This pattern ensures the LLM is **never called** without confirmed payment.

## Trust Model

PlebChat uses a **non-custodial** design where user funds are held client-side:

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT SIDE                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    CypherTap Component                   │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │    │
│  │  │ User Wallet │  │   Tokens    │  │  Default Mint   │  │    │
│  │  │ (browser)   │──│   (ecash)   │──│  (minibits)     │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              │ ecash token                       │
│                              ▼                                   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SERVER SIDE                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  PlebChat Backend                        │    │
│  │  - Validates token from TRUSTED mints only               │    │
│  │  - Redeems token (non-custodial: immediate use)          │    │
│  │  - Auto-payouts to operator's Lightning address          │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Client holds funds**: CypherTap stores user tokens in the browser. The backend never holds user balances.

2. **Immediate redemption**: Tokens are redeemed immediately upon receipt and cannot be refunded. This is payment for service.

3. **Trusted mints only**: The backend only accepts tokens from explicitly trusted mints. Tokens from other mints are rejected.

4. **No cross-mint swapping**: We don't convert tokens between mints. Users must use a mint that the backend trusts.

5. **Operator payouts**: Received funds are automatically paid out to the operator's Lightning address, minimizing hot wallet exposure.

---

## Wallet API Endpoints

All wallet endpoints are prefixed with `/api/wallet`.

### POST /check

Validate a token without redeeming it. Returns format validity, spend state, and amount.

**Request:**
```json
{
  "token": "cashuBo2F0gaJhaUgA2..."
}
```

**Response:**
```json
{
  "valid": true,
  "spent": false,
  "amount": 50,
  "error": null
}
```

### POST /receive

Redeem an ecash token to the backend wallet.

**Request:**
```json
{
  "token": "cashuBo2F0gaJhaUgA2..."
}
```

**Response:**
```json
{
  "success": true,
  "amount": 50,
  "error": null,
  "mint": "https://mint.minibits.cash/Bitcoin"
}
```

### GET /balance

Get the current wallet balance.

**Response:**
```json
{
  "balance": 1250,
  "unit": "sat"
}
```

### GET /stats

Get detailed wallet statistics (useful for debugging).

**Response:**
```json
{
  "balance": 1250,
  "unit": "sat",
  "mint_url": "https://mint.minibits.cash/Bitcoin",
  "keyset_count": 3,
  "proof_count": 42,
  "data_dir": "/app/backend/data",
  "initialized": true
}
```

---

## Admin API Endpoints

Admin endpoints require NIP-98 authentication and are prefixed with `/api/admin`.

### Authentication

All admin endpoints (except `/auth/info`) require a valid NIP-98 Authorization header:

```
Authorization: Nostr <base64-encoded-signed-event>
```

The event must be:
- Kind 27235 (NIP-98 HTTP Auth)
- Signed by a pubkey listed in `ADMIN_NPUBS`
- Less than 60 seconds old
- Include `u` tag with the request URL
- Include `method` tag with the HTTP method
- Include `payload` tag with SHA256 hash of request body (for POST)

### GET /auth/info

Check authentication status without requiring admin access.

**Response:**
```json
{
  "authenticated": true,
  "pubkey": "abc123...",
  "npub": "npub1abc...",
  "is_admin": true
}
```

### GET /stats

Get detailed wallet statistics (admin-only version).

**Response:**
```json
{
  "balance": 1250,
  "unit": "sat",
  "mint_url": "https://mint.minibits.cash/Bitcoin",
  "keyset_count": 3,
  "proof_count": 42,
  "data_dir": "/app/backend/data",
  "initialized": true,
  "admin_pubkey": "abc123..."
}
```

### POST /withdraw

Generate an ecash token for a specified amount.

**Request:**
```json
{
  "amount": 500,
  "memo": "Withdrawal to external wallet"
}
```

**Response:**
```json
{
  "success": true,
  "token": "cashuBo2F0gaJhaUgA2...",
  "amount": 500,
  "error": null
}
```

### POST /sweep

Generate a single ecash token containing all wallet funds.

**Response:**
```json
{
  "success": true,
  "token": "cashuBo2F0gaJhaUgA2...",
  "amount": 1250,
  "error": null
}
```

### POST /payout

Send funds to a Lightning address via LNURL-pay.

**Request:**
```json
{
  "amount": 500,
  "ln_address": "user@getalby.com"
}
```

Both fields are optional:
- If `amount` is omitted, sends the full balance
- If `ln_address` is omitted, uses the configured `PAYOUT_LN_ADDRESS`

**Response:**
```json
{
  "success": true,
  "amount_sent": 490,
  "fee_paid": 10,
  "error": null
}
```

---

## Admin Panel

The admin panel is a Svelte 5 application located in `admin/` that provides a web interface for wallet management.

### Features

1. **Nostr Authentication** - Uses NIP-07 browser extension (Alby, nos2x, etc.) for signing NIP-98 auth events
2. **Wallet Stats** - Real-time view of balance, proof count, keyset count, payout status, and connection status
3. **Withdrawals** - Generate ecash tokens for specific amounts with optional memos
4. **Sweep** - Generate a single token containing all funds
5. **Lightning Payout** - Send funds directly to a Lightning address

### Access Control

- Only pubkeys listed in the `ADMIN_NPUBS` environment variable can access admin features
- The panel shows "Access Denied" for authenticated users who aren't admins
- All operations require fresh NIP-98 signatures (60-second expiry)

### UI Components

- **Stats Card** - Displays balance (highlighted in cyan), proof count, keyset count, and connection status
- **Withdraw Card** - Amount input, optional memo, generates copyable token
- **Sweep Card** - One-click sweep all funds with copyable token output
- **CypherTap Component** - Handles Nostr login/logout in the header

---

## Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `WALLET_MNEMONIC` | BIP39 mnemonic (12 or 24 words) for deterministic wallet |
| `ADMIN_NPUBS` | Comma-separated list of admin npubs or hex pubkeys |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CASHU_MINT_URL` | `https://mint.minibits.cash/Bitcoin` | Primary Cashu mint URL |
| `TRUSTED_MINTS` | - | Comma-separated list of additional trusted mint URLs |
| `PAYOUT_LN_ADDRESS` | - | Lightning address for automatic payouts (e.g., `user@getalby.com`) |
| `PAYOUT_THRESHOLD_SATS` | `1000` | Minimum balance to trigger automatic payout |
| `PAYOUT_INTERVAL_SECONDS` | `300` | Payout check interval (5 minutes) |
| `FRONTEND_URL` | - | Frontend URL for CORS |
| `ADMIN_FRONTEND_URL` | - | Admin panel URL for CORS |
| `HOST` | `0.0.0.0` | Server bind host |
| `PORT` | `8000` | Server bind port |

### Generating a Wallet Mnemonic

```bash
cd backend
source venv/bin/activate
python scripts/generate_mnemonic.py           # 12 words (default)
python scripts/generate_mnemonic.py --24      # 24 words
```

```bash
python -c "from mnemonic import Mnemonic; print(Mnemonic('english').generate())"
```

---

## CashuService

The `CashuService` class wraps the nutshell (cashu) library to provide:

### Key Methods

| Method | Description |
|--------|-------------|
| `initialize()` | Initialize wallet with database and load keysets |
| `validate_token_format(token, check_mint)` | Check if token is valid cashuA/cashuB format and from trusted mint |
| `get_token_amount(token)` | Get the sats value of a token without redeeming |
| `check_token_spent(token)` | Query mint to check if token proofs are spent |
| `receive_token(token)` | Redeem token to wallet (swap proofs with mint) |
| `generate_token(amount, memo)` | Create a token from wallet balance |
| `sweep_all(memo)` | Generate token with all available funds |
| `payout_to_lightning(amount, ln_address)` | Send funds to Lightning address via LNURL-pay |
| `start_payout_task()` | Start the periodic automatic payout background task |
| `stop_payout_task()` | Stop the periodic payout background task |
| `get_stats()` | Get wallet statistics including payout configuration |
| `is_trusted_mint(mint_url)` | Check if a mint URL is in the trusted list |

### Concurrency Handling

The service uses a two-layer approach for safe concurrent access:

1. **Library-level locking**: The cashu library uses SQLite table locking (`lock_table="keysets"`) in `generate_n_secrets()` to prevent counter race conditions during secret derivation.

2. **Application-level mutex**: An `asyncio.Lock` serializes all redemption operations for defense-in-depth, ensuring clean error recovery.

```python
async with self._redemption_lock:
    return await self._redeem_token_internal(token)
```

### Error Recovery

If an "outputs already signed" error occurs (counter desync with mint):

1. The service attempts automatic recovery using the library's `restore_tokens_for_keyset()` method
2. This queries the mint to find the next unused counter position
3. If recovery succeeds, the redemption is retried automatically
4. If recovery fails, the token is logged for manual recovery

### Database Persistence

The wallet uses SQLite for persistent storage:

- **Location:** `backend/data/plebchat_wallet.sqlite3`
- **Contents:** Proofs, keysets, secret derivation counters, mint info
- **Deterministic:** Uses BIP32 derivation from mnemonic for reproducible secrets

### Mnemonic Security

On startup, the service logs important security reminders:

- **With mnemonic**: Warns to backup `WALLET_MNEMONIC` securely
- **Without mnemonic**: Critical warning that auto-generated keys are NOT persisted and funds will be LOST on restart

### Multi-Mint Support & Trust Model

The backend accepts tokens from multiple trusted mints but **does not perform cross-mint swapping**.

#### Design Decision: No Cross-Mint Swapping

We intentionally do not swap tokens from untrusted mints to a trusted mint. This decision is based on:

1. **Non-Custodial Architecture**: PlebChat uses the CypherTap component on the client side to hold user funds. The backend is a simple payment receiver, not a custodial wallet service.

2. **Complexity vs. Benefit**: Cross-mint swapping would add:
   - Lightning routing fees (typically 1-2% of the payment)
   - Additional latency for each token redemption
   - Complex failure handling for partial payments
   - Risk of stuck funds during Lightning payment failures

3. **User Choice**: The CypherTap component uses a default mint. Users who configure their client to use a different mint should ensure it's one the backend trusts.

4. **Simplicity**: Rejecting untrusted tokens with a clear error message is simpler, more predictable, and has no hidden fees.

#### Future Considerations

If mint ecosystems evolve significantly (e.g., a mint shuts down), we may revisit this decision. Potential future enhancements:

- **Mint migration notifications**: Alert users when their mint is being deprecated
- **Opt-in cross-mint swapping**: Allow admins to enable swapping for specific scenarios
- **Multiple default mints**: Support for CypherTap to use multiple mints

#### Configuration

1. **Primary mint**: Set via `CASHU_MINT_URL` (always trusted)
2. **Additional mints**: Set via `TRUSTED_MINTS` (comma-separated list)

Tokens from untrusted mints are rejected with a clear error message listing the trusted mints. Users must generate new tokens from a trusted mint to proceed.

### Automatic Lightning Payouts

When configured, the backend automatically sends funds to a Lightning address:

1. **Configuration**:
   - `PAYOUT_LN_ADDRESS`: Lightning address (e.g., `user@getalby.com`)
   - `PAYOUT_THRESHOLD_SATS`: Minimum balance to trigger payout (default: 1000)
   - `PAYOUT_INTERVAL_SECONDS`: Check interval (default: 300 = 5 min)

2. **How it works**:
   - Background task checks balance every 5 minutes
   - If balance >= threshold, initiates payout
   - Uses LNURL-pay to get invoice from Lightning address
   - Uses mint's melt capability to pay the invoice
   - Logs success/failure with amounts and fees

3. **Manual payout**: Use the `/api/admin/payout` endpoint for on-demand payouts

---

## NIP-98 Authentication

The backend implements [NIP-98](https://github.com/nostr-protocol/nips/blob/master/98.md) HTTP authentication:

### How It Works

1. Client creates a kind 27235 Nostr event with:
   - `u` tag: Request URL
   - `method` tag: HTTP method (GET, POST, etc.)
   - `payload` tag: SHA256 hash of request body (for POST/PUT/PATCH)
2. Client signs the event with their Nostr private key
3. Client base64-encodes the signed event
4. Client sends: `Authorization: Nostr <base64-event>`
5. Server decodes, verifies signature, checks expiry, validates URL/method

### Verification Steps

1. Decode base64 event from header
2. Verify event kind is 27235
3. Verify Schnorr signature against pubkey
4. Verify event is less than 60 seconds old
5. Verify URL tag matches request URL
6. Verify method tag matches request method
7. Verify payload hash matches body (if present)
8. Verify pubkey is in allowed list (for admin endpoints)

---

## Running the Backend

### Development

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -e .

# Set required environment variables
export WALLET_MNEMONIC="your twelve or twenty four word mnemonic phrase here"
export ADMIN_NPUBS="npub1youradminpubkey..."

# Run with auto-reload
python -m src.main
```

### Production

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

---

## Error Handling

### Token Errors

| Error | Cause | User Action |
|-------|-------|-------------|
| "Empty token" | No token provided | Include token in request |
| "Invalid token format" | Not cashuA/cashuB | Check token encoding |
| "Token contains no proofs" | Malformed token | Generate new token |
| "Token from untrusted mint" | Mint not in TRUSTED_MINTS | Use token from a trusted mint |
| "Token already spent" | Proofs used elsewhere | Generate new token |
| "Insufficient amount" | Token value too low | Use larger token |
| "Counter sync error" | Mint counter desync | Retry or contact support |

### Admin Errors

| HTTP Code | Error | Cause |
|-----------|-------|-------|
| 401 | "Missing Authorization header" | No auth header provided |
| 401 | "Invalid event signature" | Signature verification failed |
| 401 | "Event expired" | Event older than 60 seconds |
| 401 | "Pubkey not authorized" | Pubkey not in ADMIN_NPUBS |
| 503 | "No admin pubkeys configured" | ADMIN_NPUBS not set |
