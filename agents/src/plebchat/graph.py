"""LangGraph agent for PlebChat AI chat assistant.

This is a simple conversational AI agent that:
1. Validates and REDEEMS ecash payment tokens BEFORE LLM call
2. Processes user messages with an LLM only after payment confirmed
3. Returns refund token if redemption fails

Payment flow (redeem-first):
1. Client sends ecash token with message
2. validate_payment node checks token format AND redeems it immediately
3. If redemption fails: STOP, return token for client-side refund
4. If redemption succeeds: proceed to LLM (we've been paid)
5. On LLM failure: user loses payment (we already did the work of receiving)

This ensures we NEVER call the LLM without confirmed payment.
"""

from __future__ import annotations

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
    payment_validated: bool  # Token validated AND redeemed successfully
    payment_redeemed: bool  # Whether the token was actually redeemed
    refund: bool  # Signal client to self-redeem on error
    refund_token: str | None  # Token to return for refund (unredeemed)
    error: str | None  # Error message if request failed
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
# PRICING CONFIGURATION
# =============================================================================

# Debug/Testing mode - when enabled, all prompts cost 1 sat
# Set via PLEBCHAT_DEBUG_MODE environment variable
DEBUG_MODE = os.getenv("PLEBCHAT_DEBUG_MODE", "true").lower() in ("true", "1", "yes")
DEBUG_MODE_COST = 1  # Cost per prompt in debug mode

# Agent pricing in sats (from docs/index.md)
AGENT_PRICING = {
    "plebchat": {"first": 50, "additional": 10},
    "deep_research": {"first": 150, "additional": 200},
    "socratic_coach": {"first": 50, "additional": 0},  # Unable to prompt again
    "tldr_summarizer": {"first": 150, "additional": 200},
    "nsfw": {"first": 70, "additional": 20},
}

# Default pricing for unknown agents
DEFAULT_PRICING = {"first": 50, "additional": 10}


def get_required_amount(agent_id: str = "plebchat", is_first_message: bool = True) -> int:
    """Get the required payment amount for an agent.
    
    In DEBUG_MODE, all prompts cost 1 sat for testing.
    
    Args:
        agent_id: The agent identifier
        is_first_message: Whether this is the first message in a conversation
        
    Returns:
        Required amount in sats
    """
    if DEBUG_MODE:
        return DEBUG_MODE_COST
    pricing = AGENT_PRICING.get(agent_id, DEFAULT_PRICING)
    return pricing["first"] if is_first_message else pricing["additional"]


# =============================================================================
# PAYMENT VALIDATION
# =============================================================================


async def validate_token_with_backend(
    token: str, required_amount: int
) -> tuple[bool, int, str | None]:
    """Validate token via backend - checks format, spend state, and amount.
    
    Args:
        token: The cashu ecash token string
        required_amount: Minimum amount required in sats
        
    Returns:
        Tuple of (is_valid, actual_amount, error_message)
    """
    wallet_url = os.getenv("WALLET_URL", "http://localhost:8000/api/wallet")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{wallet_url}/check",
                json={"token": token},
                timeout=30.0,
            )
            
            if response.status_code != 200:
                print(f"[Payment] Backend check failed: {response.status_code}")
                return False, 0, f"Backend error: {response.status_code}"
            
            result = response.json()
            
            if not result.get("valid"):
                error = result.get("error", "Invalid token")
                print(f"[Payment] Token invalid: {error}")
                return False, 0, error
            
            if result.get("spent"):
                print("[Payment] Token already spent")
                return False, 0, "Token already spent"
            
            actual_amount = result.get("amount", 0)
            
            if actual_amount < required_amount:
                error = f"Insufficient amount: {actual_amount} < {required_amount} sats required"
                print(f"[Payment] {error}")
                return False, actual_amount, error
            
            print(f"[Payment] Token validated: {actual_amount} sats (required: {required_amount})")
            return True, actual_amount, None
            
    except httpx.TimeoutException:
        print("[Payment] Backend timeout during validation")
        return False, 0, "Payment service timeout"
    except Exception as e:
        print(f"[Payment] Validation error: {e}")
        return False, 0, f"Validation failed: {str(e)}"


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
    """Validate AND redeem the ecash token BEFORE the LLM is called.
    
    This is critical: we MUST redeem the token before calling the LLM to prevent
    users from getting free LLM calls when token redemption fails after the fact.
    
    Uses the backend's /check endpoint to validate, then /receive to redeem.
    """
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
            "payment_redeemed": False,
            "refund": False,
            "refund_token": None,
            "error": None,
            "run_id": run_id,
        }

    token = payment["ecash_token"]
    
    # Determine required amount based on conversation state
    # TODO: Get agent_id from config when multiple agents are supported
    agent_id = "plebchat"
    is_first_message = len([m for m in messages if isinstance(m, HumanMessage)]) <= 1
    required_amount = get_required_amount(agent_id, is_first_message)

    # Debug mode: accept fake tokens for testing without losing funds
    if token.startswith("cashu_debug_") or token == "debug":
        print("[Payment] DEBUG MODE - accepting fake token for testing")
        agent_logger.log_payment(thread_id, run_id, "debug_mode", amount_sats=required_amount)
        return {
            "payment_validated": True,
            "payment_redeemed": False,  # Fake tokens aren't redeemed
            "refund": False,
            "refund_token": None,
            "error": None,
            "run_id": run_id,
        }
    
    # Log pricing mode
    if DEBUG_MODE:
        print(f"[Payment] DEBUG_MODE enabled - requiring only {required_amount} sat")
    else:
        print(f"[Payment] Production pricing - requiring {required_amount} sats")

    print("[Payment] ========== RECEIVED TOKEN (for recovery) ==========")
    print(f"[Payment] {token}")
    print("[Payment] ====================================================")

    # Step 1: Validate token with backend (checks format, spend state, and amount)
    is_valid, actual_amount, error = await validate_token_with_backend(token, required_amount)

    if not is_valid:
        print(f"[Payment] Token validation failed: {error}")
        print("[Payment] Returning token for client-side refund")
        agent_logger.log_payment(
            thread_id, run_id, "validation_failed", amount_sats=actual_amount, token_preview=token
        )
        return {
            "payment_validated": False,
            "payment_redeemed": False,
            "refund": True,
            "refund_token": token,  # Return token for client to reclaim
            "error": f"Payment validation failed: {error}",
            "run_id": run_id,
        }

    # Step 2: IMMEDIATELY redeem the token BEFORE calling the LLM
    # This prevents users from getting free LLM calls
    print(f"[Payment] Token validated ({actual_amount} sats), redeeming NOW...")
    redeemed = await redeem_token_to_wallet(token)
    
    if not redeemed:
        print("[Payment] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("[Payment] CRITICAL: Token redemption FAILED - blocking LLM call")
        print("[Payment] Returning token for client-side refund")
        print("[Payment] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        agent_logger.log_payment(
            thread_id, run_id, "redemption_failed", amount_sats=actual_amount, token_preview=token
        )
        return {
            "payment_validated": False,
            "payment_redeemed": False,
            "refund": True,
            "refund_token": token,  # Return token for client to reclaim
            "error": "Payment redemption failed. Your token has been returned.",
            "run_id": run_id,
        }
    
    print(f"[Payment] Token redeemed successfully ({actual_amount} sats) - proceeding to LLM")
    agent_logger.log_payment(
        thread_id, run_id, "redeemed", amount_sats=actual_amount, token_preview=token
    )
    return {
        "payment_validated": True,
        "payment_redeemed": True,
        "refund": False,
        "refund_token": None,
        "error": None,
        "run_id": run_id,
    }


async def agent_node(state: AgentState, config: RunnableConfig) -> dict:
    """Process the user's message with the LLM."""
    thread_id = get_thread_id(config)
    run_id = state.get("run_id", "unknown")

    # If payment validation failed, return error with refund info
    if not state.get("payment_validated", True):
        error_msg = state.get("error") or "Payment validation failed"
        refund_token = state.get("refund_token")
        agent_logger.log_run_end(
            thread_id, run_id, success=False, error=error_msg, refund=True
        )
        return {
            "messages": [
                AIMessage(
                    content=f"Payment failed: {error_msg}. Your token has been returned for a refund."
                )
            ],
            "refund": True,
            "refund_token": refund_token,
            "error": error_msg,
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

        return {"messages": [response], "error": None}

    except Exception as e:
        error_msg = str(e)
        print(f"[Agent] LLM processing failed: {error_msg}")
        agent_logger.log_run_end(thread_id, run_id, success=False, error=error_msg, refund=False)
        # Note: Payment was already redeemed before reaching this point,
        # so we cannot offer a refund if the LLM fails. This is intentional -
        # we've already done the work of receiving the payment.
        return {
            "messages": [
                AIMessage(
                    content="Sorry, I encountered an error processing your request. "
                    "Please try again with a new payment."
                )
            ],
            "refund": False,
            "refund_token": None,
            "error": f"LLM error: {error_msg}",
        }


async def finalize_node(state: AgentState, config: RunnableConfig) -> dict:
    """Finalize the conversation. Payment was already redeemed before LLM call."""
    thread_id = get_thread_id(config)
    run_id = state.get("run_id", "unknown")

    # Payment was already redeemed in validate_payment_node BEFORE the LLM call.
    # This node just logs the successful completion.
    
    was_redeemed = state.get("payment_redeemed", False)
    if was_redeemed:
        print("[Payment] Run complete - payment was redeemed before LLM call")
    
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
