"""
LLM configuration for the agentic investigation pipeline.

The model is controlled by the LLM_MODEL_ARN env var and defaults to
Haiku 4.5 via a tagged application inference profile.
"""

import os
import logging

from langchain_groq import ChatGroq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "openai/gpt-oss-120b"

_MODEL_NAME = os.getenv("LLM_MODEL_NAME", _DEFAULT_MODEL)

_llm_instance: ChatGroq | None = None


def get_model_id() -> str:
    """Return the active model ARN for audit logging."""
    return _MODEL_NAME


def extract_token_usage(raw_message) -> dict:
    """Extract token usage from a raw AIMessage, returning empty dict on failure."""
    meta = getattr(raw_message, "usage_metadata", None)
    if not meta:
        return {}
    return {
        "input_tokens": meta.get("input_tokens", 0),
        "output_tokens": meta.get("output_tokens", 0),
        "total_tokens": meta.get("total_tokens", 0),
    }


def get_llm() -> ChatGroq:
    """Singleton accessor for the investigation LLM."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatGroq(
            model=_MODEL_NAME,
            temperature=0.1,
            api_key=os.getenv("GROQ_API_KEY"),
        )
        logger.info("ChatGroq initialised (model=%s)", _MODEL_NAME)
    return _llm_instance


def _is_retryable(exc: BaseException) -> bool:
    """Return True for transient Bedrock / network errors worth retrying."""
    # Handle botocore ClientError by inspecting the error code
    resp = getattr(exc, "response", None)
    if resp and isinstance(resp, dict):
        code = resp.get("Error", {}).get("Code", "")
        if code in ("ThrottlingException", "ServiceUnavailableException",
                     "ModelTimeoutException", "TooManyRequestsException"):
            return True

    name = type(exc).__name__
    if name in ("ThrottlingException", "ServiceUnavailableException", "ModelTimeoutException"):
        return True
    msg = str(exc).lower()
    if any(kw in msg for kw in ("throttl", "timeout", "rate exceeded", "service unavailable", "failed to parse tool call arguments", "tool_use_failed")):
        return True
    return False


@retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=15),
    reraise=True,
)
def invoke_with_retry(llm, messages):
    """Invoke an LLM (or structured-output wrapper) with retry on transient errors."""
    return llm.invoke(messages)
