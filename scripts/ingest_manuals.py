"""
fixer.ai — Ingestion Script
Runs full ingestion for:
- Tier 1: Shared equipment manuals in data/manuals/ -> tier1__{model_slug}
- Tier 2: Resolved historical tickets from SQLite -> tier2__{machine_id}
"""
import sys
from pathlib import Path

# Add project root to sys.path
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from backend.rag.ingestion import run_full_ingestion


def main():
    print("=" * 60)
    print("  fixer.ai — Chroma RAG Ingestion Pipeline")
    print("=" * 60)
    
    results = run_full_ingestion()
    
    print("\n" + "=" * 60)
    print("  INGESTION SUMMARY")
    print("=" * 60)
    print("\nTier 1 (Shared Manual Collections):")
    for model, count in results["tier1"].items():
        print(f"  • tier1__{model}: {count} chunks")
    
    print("\nTier 2 (Isolated Machine Collections):")
    for m_id, count in results["tier2"].items():
        print(f"  • tier2__{m_id.replace('-', '_')}: {count} tickets")
    
    print("\n✅ All RAG collections successfully populated.")


if __name__ == "__main__":
    main()
