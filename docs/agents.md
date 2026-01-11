# PlebChat Agent Architecture

The PlebChat agent is a LangGraph-based AI assistant that validates Bitcoin ecash payments before processing requests. This document describes the agent architecture, LLM provider configuration, and payment validation flow.

## LLM Provider Configuration

The agent supports two LLM providers that can be selected via the `LLM_PROVIDER` environment variable:

### PlebChat Provider (Default)

Uses any OpenAI-compatible API endpoint. This includes:

- **Ollama**: Local LLM inference (`http://localhost:11434/v1`)
- **LM Studio**: Local model hosting (`http://localhost:1234/v1`)
- **vLLM**: High-performance inference server
- **Any OpenAI-compatible API**

**Required environment variables:**

```bash
LLM_PROVIDER=plebchat
LLM_BASE_URL=http://localhost:11434/v1  # Your endpoint
LLM_MODEL=llama3.2                       # Your model name
LLM_API_KEY=not_set                      # Optional for local endpoints
```

### Grok Provider

Uses xAI's Grok API with `grok-4-fast-non-thinking` model.

**Required environment variables:**

```bash
LLM_PROVIDER=grok
XAI_API_KEY=your-xai-api-key            # Get from https://console.x.ai/
XAI_DEFAULT_MODEL=grok-4-fast-non-thinking  # Optional, this is the default
```

## Agent Graph Architecture

The agent follows a **payment-first, redeem-before-LLM** pattern implemented as a simple LangGraph state machine:

```
┌─────────────┐    ┌──────────────────┐    ┌───────┐    ┌──────────┐    ┌─────┐
│   START     │───>│ validate_payment │───>│ agent │───>│ finalize │───>│ END │
└─────────────┘    └──────────────────┘    └───────┘    └──────────┘    └─────┘
                            │
                            │ (validation failed)
                            └────────────────────────────────────────────>─┘
```

### Graph Nodes

1. **validate_payment**: Validates and redeems ecash token BEFORE LLM call
   - Checks token format via backend `/api/wallet/check`
   - Verifies token is unspent and has sufficient amount
   - Redeems token to wallet via `/api/wallet/receive`
   - If redemption fails, returns token for client-side refund

2. **agent**: Processes user message with the configured LLM
   - Only executes if payment was validated and redeemed
   - Uses system prompt to guide responses
   - Streams response back to client

3. **finalize**: Logs completion of successful runs
   - Confirms payment was redeemed
   - Records final response for auditing

### State Management

```python
class AgentState(TypedDict):
    messages: list[BaseMessage]      # Conversation history
    payment: PaymentInfo | None      # Ecash token and amount
    payment_validated: bool          # Token validated AND redeemed
    payment_redeemed: bool           # Whether token was actually redeemed
    refund: bool                     # Signal client to self-redeem
    refund_token: str | None         # Token to return for refund
    error: str | None                # Error message if failed
    run_id: str | None               # Unique ID for logging
```

## Payment Validation Flow

The agent validates payment in this order:

1. **Token Format Check**: Verifies `cashuA` or `cashuB` prefix
2. **Spend State Check**: Queries mint for token spend status
3. **Amount Validation**: Ensures token value meets required amount
4. **Immediate Redemption**: Redeems token to wallet BEFORE calling LLM

This "redeem-first" approach ensures:
- No free LLM calls (payment confirmed before processing)
- Clear refund path (unredeemed tokens returned to client)
- Atomic payment (either we have the funds or we don't proceed)

## Pricing

Pricing is configured per agent (in satoshis):

| Agent | First Message | Additional Messages |
|-------|---------------|---------------------|
| plebchat | 50 sats | 10 sats |
| deep_research | 150 sats | 200 sats |
| socratic_coach | 50 sats | 0 sats (single-shot) |
| tldr_summarizer | 150 sats | 200 sats |
| nsfw | 70 sats | 20 sats |

**Debug Mode**: Set `VITE_DEBUG=1` in frontend to show testnet badge in navbar.

## Configuration Reference

### Environment Variables

| Variable | Provider | Required | Description |
|----------|----------|----------|-------------|
| `LLM_PROVIDER` | Both | No | `plebchat` (default) or `grok` |
| `LLM_BASE_URL` | plebchat | Yes | OpenAI-compatible endpoint URL |
| `LLM_MODEL` | plebchat | Yes | Model name (e.g., `llama3.2`) |
| `LLM_API_KEY` | plebchat | No | API key (some endpoints don't need it) |
| `XAI_API_KEY` | grok | Yes | xAI API key from console.x.ai |
| `XAI_DEFAULT_MODEL` | grok | No | Grok model (default: `grok-4-fast-non-thinking`) |
| `WALLET_URL` | Both | No | Backend wallet URL (default: `http://localhost:8000/api/wallet`) |
| `VITE_DEBUG` | Frontend | No | Set to `1` to show testnet badge in navbar |

### Example Configurations

**Local Ollama setup:**
```bash
LLM_PROVIDER=plebchat
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.2
```

**xAI Grok setup:**
```bash
LLM_PROVIDER=grok
XAI_API_KEY=xai-xxxxxxxxxxxxxxxxx
```

## Development

Run the agent in development mode:

```bash
cd agents
source .venv/bin/activate
langgraph dev
```

The agent will be available at `http://localhost:2024`.

## Logging

All agent runs are logged to `logs/{thread_id}.jsonl` with events:
- `run_start`: Initial request
- `payment_validated` / `payment_redeemed`: Payment status
- `llm_response`: LLM output
- `run_end`: Completion status
