"""
Local text embeddings using sentence-transformers.

Replaces the AWS Bedrock Titan embedding backend which is blocked by an
organisation-level Service Control Policy (SCP) on this account.

Model   : all-MiniLM-L6-v2  (22 MB, CPU-friendly)
Dims    : 384
API     : identical to the old bedrock/embeddings.py — get_embedding() and
          get_batch_embeddings() are the only two symbols imported elsewhere.

The MongoDB Atlas Vector Search index must use numDimensions=384.
Run the seed_transactions.py script after changing this file so all stored
transaction vectors are regenerated at 384 dims.
"""

import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton — loaded once, reused across requests
# ---------------------------------------------------------------------------
_model = None


def _get_model():
    """Load (or return cached) SentenceTransformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            model_name = os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            logger.info(f"Loading local embedding model: {model_name}")
            _model = SentenceTransformer(model_name)
            logger.info(f"Local embedding model loaded. Dimensions: {_model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load sentence-transformers model: {e}")
            raise
    return _model


# ---------------------------------------------------------------------------
# Public API  (same signatures as the old Bedrock version)
# ---------------------------------------------------------------------------

async def get_embedding(text: str) -> List[float]:
    """
    Generate a 384-dimensional embedding for *text* using the local model.

    Raises on failure so the caller's except block triggers the field-based
    fallback (same behaviour as when Bedrock was unavailable).
    """
    try:
        model = _get_model()
        embedding = model.encode(text, convert_to_numpy=True).tolist()
        return embedding
    except Exception as e:
        logger.error(f"Error generating local embedding: {e}")
        raise


async def get_batch_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts (batched for efficiency)."""
    try:
        model = _get_model()
        embeddings = model.encode(texts, convert_to_numpy=True).tolist()
        return embeddings
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {e}")
        raise


# ---------------------------------------------------------------------------
# Backwards-compat stubs — nothing outside this file uses these directly,
# but keeping them avoids import errors if any script imports the old class.
# ---------------------------------------------------------------------------

class BedrockTitanEmbeddings:
    """Stub kept for import compatibility. Not functional."""
    def __init__(self, *args, **kwargs):
        logger.warning("BedrockTitanEmbeddings is deprecated — using local sentence-transformers instead.")

    def predict(self, text: str) -> List[float]:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(get_embedding(text))


def get_embedding_model():
    """Stub for import compatibility."""
    return _get_model()


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import asyncio

    async def _test():
        emb = await get_embedding("Suspicious transaction from unknown device at unusual location.")
        print(f"Embedding dimensions: {len(emb)}")
        print(f"First 5 values: {emb[:5]}")

        batch = await get_batch_embeddings([
            "Large cash withdrawal in foreign country",
            "Regular grocery purchase at local supermarket",
        ])
        print(f"Batch: {len(batch)} embeddings, each {len(batch[0])} dims")

    asyncio.run(_test())