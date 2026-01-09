"""LangGraph agent for PlebChat AI chat assistant.

This is a simple conversational AI agent that:
1. Validates ecash payment tokens
2. Processes user messages with an LLM
3. Redeems payment tokens on successful completion

Payment flow (validate-then-redeem-on-success):
1. Client sends ecash token with message
2. validate_payment node checks token format (doesn't redeem yet)
3. agent node processes the LLM request
4. On SUCCESS: redeem token to backend wallet
5. On FAILURE: don't redeem, return refund flag so client can self-recover
"""

from __future__ import annotations

import base64
import os
import uuid
from typing import Annotated, Literal, TypedDict

import httpx
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from src.plebchat.logging import agent_logger


def get_thread_id(config: RunnableConfig | None) -> str:
    """Extract thread_id from LangGraph config."""
    if config is None:
        return "unknown"
    configurable = config.get("configurable", {})
    return configurable.get("thread_id", "unknown")


# =============================================================================
# STATE DEFINITIONS
# =============================================================================


class PaymentInfo(TypedDict, total=False):
    """Payment information from client."""

    ecash_token: str  # Cashu ecash token
    amount_sats: int  # Expected amount in sats
    mint: str | None  # Mint URL


class AgentState(TypedDict):
    """State for the PlebChat agent."""

    messages: Annotated[list[BaseMessage], add_messages]
    payment: PaymentInfo | None
    payment_validated: bool  # Token checked but not redeemed
    payment_token: str | None  # Token to redeem on success
    refund: bool  # Signal client to self-redeem on error
    run_id: str | None  # Unique ID for this run (for logging)


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """You are PlebChat, a helpful AI assistant. You provide clear, concise, and accurate responses to user questions.

Guidelines:
- Be friendly and conversational
- Provide direct answers without unnecessary preamble
- If you don't know something, say so honestly
- Keep responses focused and relevant to the question
"""


# =============================================================================
# MODEL CREATION
# =============================================================================


def create_model():
    """Create the LLM model using OpenAI-compatible endpoint.

    Requires explicit configuration - does NOT default to OpenAI.
    Works with any OpenAI-compatible API (Ollama, vLLM, LM Studio, etc.)
    """
    base_url = os.getenv("LLM_BASE_URL")
    api_key = os.getenv("LLM_API_KEY")
    model_name = os.getenv("LLM_MODEL")

    if not base_url:
        raise ValueError(
            "LLM_BASE_URL environment variable is required. "
            "Set it to your OpenAI-compatible endpoint (e.g., http://localhost:11434/v1 for Ollama)"
        )

    if not model_name:
        raise ValueError(
            "LLM_MODEL environment variable is required. "
            "Set it to your model name (e.g., llama3.2, mistral, etc.)"
        )

    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key or "not-needed",  # Some endpoints don't require a key
        model=model_name,
        temperature=0.7,
        streaming=True,
    )


# =============================================================================
# PAYMENT VALIDATION
# =============================================================================


def validate_token_format(token: str) -> bool:
    """Validate that a string looks like a valid Cashu token.

    Cashu tokens have two formats:
    - cashuA: base64url encoded JSON
    - cashuB: base64url encoded CBOR (binary)

    We just check the prefix and that it's valid base64url.
    Actual validation happens when the backend tries to redeem it.
    """
    try:
        if not (token.startswith("cashuA") or token.startswith("cashuB")):
            print(f"[Payment] Unknown token format: {token[:10]}...")
            return False

        token_data = token[6:]
        padding = 4 - len(token_data) % 4
        if padding != 4:
            token_data += "=" * padding

        decoded = base64.urlsafe_b64decode(token_data)

        if len(decoded) < 10:
            print("[Payment] Token data too short")
            return False

        token_type = "CBOR" if token.startswith("cashuB") else "JSON"
        print(f"[Payment] Token format valid: {token_type}, {len(decoded)} bytes")
        return True

    except Exception as e:
        print(f"[Payment] Token format validation failed: {e}")
        return False


async def validate_token_state(token: str) -> tuple[bool, str | None]:
    """Validate that a Cashu token has valid format."""
    if not validate_token_format(token):
        return False, None
    print("[Payment] Token format validated, will attempt redemption on success")
    return True, None


async def redeem_token_to_wallet(token: str) -> bool:
    """Redeem a Cashu token to the backend wallet service."""
    wallet_url = os.getenv("WALLET_URL", "http://localhost:8000/api/wallet")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{wallet_url}/receive",
                json={"token": token},
                timeout=30.0,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    amount = result.get("amount", 0)
                    print(f"[Payment] Successfully redeemed {amount} sats to wallet")
                    return True
                else:
                    print(f"[Payment] Wallet rejected token: {result.get('error')}")
                    return False
            else:
                print(f"[Payment] Failed to redeem: {response.text}")
                return False

    except Exception as e:
        print(f"[Payment] Redemption error: {e}")
        return False


# =============================================================================
# GRAPH NODES
# =============================================================================


async def validate_payment_node(state: AgentState, config: RunnableConfig) -> dict:
    """Validate the ecash token WITHOUT redeeming it."""
    # Get thread_id and run_id for logging
    thread_id = get_thread_id(config)
    run_id = state.get("run_id") or str(uuid.uuid4())

    # Extract first human message for logging
    messages = state.get("messages", [])
    first_message = ""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            first_message = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    # Log run start
    agent_logger.log_run_start(
        thread_id=thread_id,
        run_id=run_id,
        message=first_message,
        payment=state.get("payment"),
    )

    payment = state.get("payment")

    # If no payment provided, skip validation (free mode for development)
    if not payment or not payment.get("ecash_token"):
        print("[Payment] No payment token provided, skipping validation (free mode)")
        agent_logger.log_payment(thread_id, run_id, "skipped", amount_sats=0)
        return {
            "payment_validated": True,
            "payment_token": None,
            "refund": False,
            "run_id": run_id,
        }

    token = payment["ecash_token"]
    amount_sats = payment.get("amount_sats", 0)

    # Debug mode: accept fake tokens for testing without losing funds
    if token.startswith("cashu_debug_") or token == "debug":
        print("[Payment] DEBUG MODE - accepting fake token for testing")
        agent_logger.log_payment(thread_id, run_id, "debug_mode", amount_sats=amount_sats)
        return {
            "payment_validated": True,
            "payment_token": None,  # Don't try to redeem debug tokens
            "refund": False,
            "run_id": run_id,
        }

    print("[Payment] ========== RECEIVED TOKEN (for recovery) ==========")
    print(f"[Payment] {token}")
    print("[Payment] ====================================================")

    is_valid, _ = await validate_token_state(token)

    if not is_valid:
        print("[Payment] Token validation failed - client should still have valid token")
        agent_logger.log_payment(
            thread_id, run_id, "validation_failed", amount_sats=amount_sats, token_preview=token
        )
        return {
            "payment_validated": False,
            "payment_token": None,
            "refund": True,
            "run_id": run_id,
        }

    print("[Payment] Token validated, will redeem on success")
    agent_logger.log_payment(
        thread_id, run_id, "validated", amount_sats=amount_sats, token_preview=token
    )
    return {
        "payment_validated": True,
        "payment_token": token,
        "refund": False,
        "run_id": run_id,
    }


async def agent_node(state: AgentState, config: RunnableConfig) -> dict:
    """Process the user's message with the LLM."""
    thread_id = get_thread_id(config)
    run_id = state.get("run_id", "unknown")

    if not state.get("payment_validated", True):
        agent_logger.log_run_end(
            thread_id, run_id, success=False, error="Payment validation failed", refund=True
        )
        return {
            "messages": [
                AIMessage(
                    content="Payment validation failed. Please try again with a valid ecash token."
                )
            ],
            "refund": True,
        }

    try:
        model = create_model()

        # Build messages with system prompt
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]

        print("[Agent] Invoking LLM...")
        response = await model.ainvoke(messages)
        print("[Agent] LLM response received")

        # Log the LLM response
        agent_logger.log_llm_response(
            thread_id=thread_id,
            run_id=run_id,
            content=response.content if isinstance(response.content, str) else str(response.content),
            finish_reason=(
                response.response_metadata.get("finish_reason")
                if hasattr(response, "response_metadata")
                else None
            ),
        )

        return {"messages": [response]}

    except Exception as e:
        print(f"[Agent] LLM processing failed: {e}")
        agent_logger.log_run_end(thread_id, run_id, success=False, error=str(e), refund=True)
        token = state.get("payment_token")
        if token:
            print("[Payment] ========== REFUNDABLE TOKEN ==========")
            print(f"[Payment] {token}")
            print("[Payment] ========================================")
        return {
            "messages": [
                AIMessage(
                    content="Sorry, I encountered an error processing your request. "
                    "Your payment has not been taken - please try again."
                )
            ],
            "refund": True,
        }


async def finalize_node(state: AgentState, config: RunnableConfig) -> dict:
    """Finalize the conversation and redeem payment if successful."""
    thread_id = get_thread_id(config)
    run_id = state.get("run_id", "unknown")
    token = state.get("payment_token")

    if token:
        print("[Payment] Attempting to redeem token to wallet...")
        redeemed = await redeem_token_to_wallet(token)
        if not redeemed:
            print("[Payment] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("[Payment] WARNING: Conversation succeeded but token redemption failed!")
            print("[Payment] UNREDEEMED TOKEN - MANUAL RECOVERY NEEDED:")
            print(f"[Payment] {token}")
            print("[Payment] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            agent_logger.log_payment(thread_id, run_id, "redemption_failed", token_preview=token)
        else:
            print("[Payment] Token redeemed successfully")
            agent_logger.log_payment(thread_id, run_id, "redeemed", token_preview=token)

    # Get final response for logging
    messages = state.get("messages", [])
    final_response = None
    if messages:
        last_msg = messages[-1]
        if isinstance(last_msg, AIMessage):
            final_response = (
                last_msg.content if isinstance(last_msg.content, str) else str(last_msg.content)
            )

    agent_logger.log_run_end(
        thread_id=thread_id,
        run_id=run_id,
        final_response=final_response,
        success=True,
        refund=False,
    )

    return {"refund": False}


# =============================================================================
# GRAPH ROUTING
# =============================================================================


def route_after_validation(state: AgentState) -> Literal["agent", "end"]:
    """Route based on payment validation result."""
    if state.get("payment_validated", True):
        return "agent"
    return "end"


# =============================================================================
# GRAPH CONSTRUCTION
# =============================================================================

# Build the graph
builder = StateGraph(AgentState)

# Add nodes
builder.add_node("validate_payment", validate_payment_node)
builder.add_node("agent", agent_node)
builder.add_node("finalize", finalize_node)

# Add edges
builder.add_edge("__start__", "validate_payment")
builder.add_conditional_edges(
    "validate_payment",
    route_after_validation,
    {"agent": "agent", "end": END},
)
builder.add_edge("agent", "finalize")
builder.add_edge("finalize", END)

# Compile the graph
graph = builder.compile()
