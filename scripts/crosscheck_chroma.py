import sys
sys.path.insert(0, '.')

import chromadb
from backend.config import CHROMA_PERSIST_DIR

client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
collections = client.list_collections()

print(f"Chroma collections ({len(collections)} total):")
tier1 = [c for c in collections if c.name.startswith("tier1")]
tier2 = [c for c in collections if c.name.startswith("tier2")]

print()
print("Tier 1 (shared manuals per model):")
for col in sorted(tier1, key=lambda c: c.name):
    count = col.count()
    status = "OK" if count > 0 else "EMPTY!"
    print(f"  {col.name}: {count} chunks [{status}]")

print()
print("Tier 2 (isolated history per machine):")
for col in sorted(tier2, key=lambda c: c.name):
    count = col.count()
    status = "OK" if count > 0 else "EMPTY!"
    print(f"  {col.name}: {count} tickets [{status}]")

# Check expected collections exist
expected_t1 = {"tier1__fanuc_arcmate100id", "tier1__haas_vf2", "tier1__generic_conveyor", "tier1__calibration_station"}
expected_t2 = {"tier2__M_01", "tier2__M_02", "tier2__M_03", "tier2__M_04"}
actual_names = {c.name for c in collections}

missing_t1 = expected_t1 - actual_names
missing_t2 = expected_t2 - actual_names
if missing_t1:
    print(f"\nMISSING Tier 1 collections: {missing_t1}")
if missing_t2:
    print(f"\nMISSING Tier 2 collections: {missing_t2}")

# Spot-check retrieval
from backend.rag.retrieval import retrieve_tier1, retrieve_tier2

print()
print("Spot-check retrieval quality:")
hits = retrieve_tier1("fanuc_arcmate100id", "J2 harmonic drive bearing grease", n=2)
print(f"  FANUC 'J2 harmonic drive': {len(hits)} results, top distance={hits[0]['distance']:.4f}" if hits else "  FANUC query returned 0 results! CHECK!")

hits2 = retrieve_tier2("M-01", "torque over-limit alarm bearing failure", n=2)
print(f"  M-01 Tier 2 'torque alarm': {len(hits2)} results" if hits2 else "  M-01 Tier 2 query returned 0 results! CHECK!")

hits3 = retrieve_tier1("haas_vf2", "spindle bearing vibration alarm 121", n=2)
print(f"  Haas VF-2 'spindle bearing': {len(hits3)} results" if hits3 else "  Haas VF-2 query returned 0 results! CHECK!")

hits4 = retrieve_tier2("M-04", "calibration drift ISO 6789", n=2)
print(f"  M-04 Tier 2 'calibration drift': {len(hits4)} results" if hits4 else "  M-04 Tier 2 query returned 0 results! CHECK!")

if not missing_t1 and not missing_t2 and hits and hits2 and hits3 and hits4:
    print()
    print("Chroma assertions PASSED")
