"""
fixer.ai — RAG Retrieval Service
Two-tier retrieval:
- Tier 1: Shared equipment manuals per machine model (e.g. fanuc_arcmate100id)
- Tier 2: Isolated ticket history per machine instance (e.g. M-01)

Provides isolated, scoped vector queries and formatted context bundles for the resolver agent.
"""
from typing import Optional
from backend.rag.chroma_client import (
    get_tier1_collection,
    get_tier2_collection,
    get_chroma_client,
)


def retrieve_tier1(
    model_slug: str,
    query: str,
    n: int = 4,
    n_results: Optional[int] = None,
    client: Optional[object] = None,
) -> list[dict]:
    """
    Retrieve top-n matching manual excerpts for a machine model.
    Shared across all machine units of the same model.
    """
    if not query.strip():
        return []

    fetch_n = n_results if n_results is not None else n

    try:
        collection = get_tier1_collection(model_slug, client=client)
        count = collection.count()
        if count == 0:
            return []

        limit = min(fetch_n, count)
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            include=["documents", "metadatas", "distances"],
        )

        items = []
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            dists = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
            ids = results["ids"][0] if results.get("ids") else [""] * len(docs)

            for doc_id, doc, meta, dist in zip(ids, docs, metas, dists):
                items.append({
                    "id": doc_id,
                    "text": doc,
                    "content": doc,
                    "metadata": meta,
                    "distance": float(dist),
                    "source": meta.get("source", ""),
                    "section": meta.get("section", ""),
                    "page": meta.get("page", None),
                })
        return items
    except Exception as e:
        print(f"Error in retrieve_tier1({model_slug}): {e}")
        return []


def retrieve_tier2(
    machine_id: str,
    query: str,
    n: int = 3,
    n_results: Optional[int] = None,
    client: Optional[object] = None,
) -> list[dict]:
    """
    Retrieve top-n matching past resolved tickets for this specific machine unit.
    STRICTLY ISOLATED: Only searches this machine's own collection.
    """
    if not query.strip():
        return []

    fetch_n = n_results if n_results is not None else n

    try:
        collection = get_tier2_collection(machine_id, client=client)
        count = collection.count()
        if count == 0:
            return []

        limit = min(fetch_n, count)
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            include=["documents", "metadatas", "distances"],
        )

        items = []
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            dists = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
            ids = results["ids"][0] if results.get("ids") else [""] * len(docs)

            for doc_id, doc, meta, dist in zip(ids, docs, metas, dists):
                items.append({
                    "id": doc_id,
                    "text": doc,
                    "content": doc,
                    "metadata": meta,
                    "distance": float(dist),
                    "ticket_id": meta.get("ticket_id", ""),
                    "failure_code": meta.get("failure_code", ""),
                    "technician_id": meta.get("technician_id", ""),
                    "severity": meta.get("severity", ""),
                })
        return items
    except Exception as e:
        print(f"Error in retrieve_tier2({machine_id}): {e}")
        return []


def retrieve_fused_context(
    machine_id: str,
    model_slug: str,
    query: str,
    n_manuals: int = 4,
    n_tickets: int = 3,
    client: Optional[object] = None,
) -> dict:
    """
    Consolidated RAG context retrieval for the resolver agent.
    Combines:
    - Tier 1: Engineering manual excerpts for the machine's model
    - Tier 2: The machine's own historical ticket resolutions
    """
    manuals = retrieve_tier1(model_slug=model_slug, query=query, n=n_manuals, client=client)
    past_tickets = retrieve_tier2(machine_id=machine_id, query=query, n=n_tickets, client=client)

    return {
        "machine_id": machine_id,
        "model_slug": model_slug,
        "query": query,
        "manual_excerpts": manuals,
        "past_tickets": past_tickets,
        "has_manual_context": len(manuals) > 0,
        "has_ticket_context": len(past_tickets) > 0,
    }
