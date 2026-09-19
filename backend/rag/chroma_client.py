"""
fixer.ai — Chroma Vector DB Client & Collection Management
Two-tier vector database architecture:
- Tier 1: Shared per machine model (manuals, engineering specs)
- Tier 2: Isolated per machine instance (individual unit resolved ticket history)

Isolation guarantee: M-01's history never leaks into M-02's collection.
"""
from pathlib import Path
from typing import Optional
import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from chromadb.utils.embedding_functions import (
    DefaultEmbeddingFunction,
    OllamaEmbeddingFunction,
)

from backend.config import (
    CHROMA_PERSIST_DIR,
    LLM_STUB_MODE,
    OLLAMA_BASE_URL,
    EMBEDDING_MODEL,
)

_client: Optional[ClientAPI] = None


def get_embedding_function():
    """
    Returns the appropriate embedding function:
    - In LLM_STUB_MODE (or when Ollama isn't configured/reachable):
      Uses Chroma's local DefaultEmbeddingFunction (ONNX MiniLM-L6-v2, 384-dim).
      Runs completely offline on CPU with zero setup and high retrieval quality.
    - In production mode with Ollama:
      Uses nomic-embed-text via OllamaEmbeddingFunction.
    """
    if LLM_STUB_MODE:
        return DefaultEmbeddingFunction()

    try:
        # Attempt to use Ollama embedding function
        return OllamaEmbeddingFunction(
            model_name=EMBEDDING_MODEL,
            url=OLLAMA_BASE_URL,
        )
    except Exception:
        # Fallback to local default if Ollama is unreachable
        return DefaultEmbeddingFunction()


def get_chroma_client(persist_directory: Optional[str] = None) -> ClientAPI:
    """
    Returns singleton Chroma PersistentClient.
    Creates directory if it does not exist.
    """
    global _client
    if _client is None or persist_directory is not None:
        target_dir = persist_directory or CHROMA_PERSIST_DIR
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=target_dir)
    return _client


def format_tier1_name(model_slug: str) -> str:
    """Format collection name for Tier 1: shared manuals per machine model."""
    clean_slug = model_slug.strip().lower().replace("-", "_").replace(" ", "_")
    return f"tier1__{clean_slug}"


def format_tier2_name(machine_id: str) -> str:
    """Format collection name for Tier 2: isolated history per machine instance."""
    clean_id = machine_id.strip().upper().replace("-", "_")
    return f"tier2__{clean_id}"


def get_tier1_collection(model_slug: str, client: Optional[ClientAPI] = None) -> Collection:
    """
    Retrieve or create Tier 1 collection for a machine model (e.g., fanuc_arcmate100id).
    Shared across all machine units of this model.
    """
    chroma = client or get_chroma_client()
    name = format_tier1_name(model_slug)
    ef = get_embedding_function()
    return chroma.get_or_create_collection(
        name=name,
        embedding_function=ef,
        metadata={"tier": "1", "model_slug": model_slug, "description": f"Manuals for {model_slug}"}
    )


def get_tier2_collection(machine_id: str, client: Optional[ClientAPI] = None) -> Collection:
    """
    Retrieve or create Tier 2 collection for a specific machine instance (e.g., M-01).
    Strictly isolated: only holds this machine unit's own resolved tickets.
    """
    chroma = client or get_chroma_client()
    name = format_tier2_name(machine_id)
    ef = get_embedding_function()
    return chroma.get_or_create_collection(
        name=name,
        embedding_function=ef,
        metadata={"tier": "2", "machine_id": machine_id, "description": f"Ticket history for {machine_id}"}
    )


def reset_test_chroma(test_dir: str) -> ClientAPI:
    """Helper for isolated unit tests to create a fresh test database."""
    import shutil
    if Path(test_dir).exists():
        shutil.rmtree(test_dir)
    Path(test_dir).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=test_dir)
