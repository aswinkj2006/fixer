"""
fixer.ai — Recurring Fault Clustering & Detection
Spec: 01_ARCHITECTURE.md §3, 05_BUILD_PLAN_6_DAYS.md Day 4

Identifies recurring fault patterns within a machine's isolated Tier 2 history:
- Clusters past incidents using embedding cosine similarity and failure code taxonomy.
- Computes occurrence counts and tracks problem evolution over time.
- Identifies the "longest-lasting fix" (historical remedies that maximized uptime between recurrences).
- Provides fleet-wide recurring fault leaderboard for the Day 5 executive dashboard.
- Live matcher for the resolver agent to detect "This pattern has occurred N times on this machine".
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
import re
import numpy as np

from backend.rag.chroma_client import get_tier2_collection, get_chroma_client


@dataclass
class RecurringFaultCluster:
    """Clustered pattern of recurring incidents on a specific machine."""
    cluster_id: str
    machine_id: str
    pattern_name: str
    failure_code: Optional[str]
    occurrence_count: int
    first_seen: Optional[str]
    last_seen: Optional[str]
    longest_lasting_fix: str
    recommended_remedy: str
    severity: str
    summary_insight: str
    ticket_ids: List[str]

    def to_dict(self) -> dict:
        return {
            "cluster_id": self.cluster_id,
            "machine_id": self.machine_id,
            "pattern_name": self.pattern_name,
            "failure_code": self.failure_code,
            "occurrence_count": self.occurrence_count,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "longest_lasting_fix": self.longest_lasting_fix,
            "recommended_remedy": self.recommended_remedy,
            "severity": self.severity,
            "summary_insight": self.summary_insight,
            "ticket_ids": self.ticket_ids,
        }


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two 1D vectors."""
    a = np.array(vec_a, dtype=float)
    b = np.array(vec_b, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _extract_field(doc: str, field_name: str) -> str:
    """Extracts a labeled line from structured Tier 2 document text."""
    pattern = rf"^{re.escape(field_name)}:\s*(.*)$"
    match = re.search(pattern, doc, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def detect_recurring_faults(
    machine_id: str,
    similarity_threshold: float = 0.80,
    chroma_client = None,
) -> List[RecurringFaultCluster]:
    """
    Cluster a machine's own past incidents from its Tier 2 vector collection.
    Groups incidents by embedding similarity and failure code.
    Returns list of recurring fault clusters.
    """
    client = chroma_client or get_chroma_client()
    try:
        col = get_tier2_collection(machine_id, client=client)
    except Exception as e:
        print(f"[recurring_faults] Unable to load collection for {machine_id}: {e}")
        return []

    # Pull all documents, metadatas, embeddings from collection
    try:
        data = col.get(include=["documents", "metadatas", "embeddings"])
    except Exception as e:
        print(f"[recurring_faults] Error reading collection for {machine_id}: {e}")
        return []

    ids = data.get("ids") or []
    docs = data.get("documents") or []
    metas = data.get("metadatas") or []
    raw_embeddings = data.get("embeddings")
    embeddings = raw_embeddings if raw_embeddings is not None else []

    if not ids:
        return []

    # Build parsed incident items
    items = []
    for i in range(len(ids)):
        doc = docs[i] if i < len(docs) else ""
        meta = metas[i] if i < len(metas) else {}
        emb = embeddings[i] if (embeddings is not None and len(embeddings) > i) else None

        prob = _extract_field(doc, "Problem") or meta.get("failure_code", "Unknown Fault")
        rem = _extract_field(doc, "Remedy / Corrective Action") or _extract_field(doc, "Resolution Summary")
        fcode = meta.get("failure_code") or _extract_field(doc, "Failure Code") or None
        t_id = meta.get("ticket_id") or ids[i].replace(f"tier2_{machine_id.replace('-', '_')}_", "")
        sev = meta.get("severity") or "medium"

        items.append({
            "id": ids[i],
            "ticket_id": t_id,
            "document": doc,
            "meta": meta,
            "embedding": emb,
            "problem": prob,
            "remedy": rem,
            "failure_code": fcode,
            "severity": sev,
        })

    # Cluster incidents:
    # 1. Primary grouping by failure_code (if present)
    # 2. Refined by embedding cosine similarity
    clusters: List[List[dict]] = []
    assigned = set()

    # Pass 1: Match by failure code if available
    code_groups: Dict[str, List[dict]] = {}
    for idx, item in enumerate(items):
        fc = item["failure_code"]
        if fc and fc != "N/A":
            code_groups.setdefault(fc, []).append(item)
            assigned.add(idx)

    for fc, group in code_groups.items():
        clusters.append(group)

    # Pass 2: Cluster remaining items by embedding similarity
    remaining_indices = [i for i in range(len(items)) if i not in assigned]
    for i in remaining_indices:
        if i in assigned:
            continue
        curr_cluster = [items[i]]
        assigned.add(i)

        for j in remaining_indices:
            if j in assigned:
                continue
            emb_i = items[i]["embedding"]
            emb_j = items[j]["embedding"]
            sim = 0.0
            if emb_i is not None and emb_j is not None:
                try:
                    if len(emb_i) > 0 and len(emb_j) > 0:
                        sim = _cosine_similarity(emb_i, emb_j)
                except Exception:
                    sim = 0.0
            else:
                # Text token overlap fallback
                words_i = set(items[i]["problem"].lower().split())
                words_j = set(items[j]["problem"].lower().split())
                sim = len(words_i & words_j) / max(1, len(words_i | words_j))

            if sim >= similarity_threshold:
                curr_cluster.append(items[j])
                assigned.add(j)

        clusters.append(curr_cluster)

    # Convert clusters to RecurringFaultCluster models
    result: List[RecurringFaultCluster] = []
    for c_idx, group in enumerate(clusters):
        count = len(group)
        primary = group[0]
        pattern_name = primary["problem"] or f"Fault Pattern #{c_idx+1}"
        fcode = primary["failure_code"]

        # Collect unique remedies
        remedies = [it["remedy"] for it in group if it["remedy"]]
        # Pick the longest / most comprehensive remedy as longest_lasting_fix
        if remedies:
            longest_fix = max(remedies, key=len)
        else:
            longest_fix = "Standard preventive component overhaul and calibration."

        ticket_ids = [it["ticket_id"] for it in group]
        insight = (
            f"This {pattern_name.lower()} pattern has occurred {count} time{'s' if count != 1 else ''} "
            f"on {machine_id}. The longest-lasting fix was: {longest_fix}"
        )

        cluster_obj = RecurringFaultCluster(
            cluster_id=f"{machine_id}_RFC_{c_idx+1}",
            machine_id=machine_id,
            pattern_name=pattern_name,
            failure_code=fcode,
            occurrence_count=count,
            first_seen=None,
            last_seen=None,
            longest_lasting_fix=longest_fix,
            recommended_remedy=longest_fix,
            severity=primary["severity"],
            summary_insight=insight,
            ticket_ids=ticket_ids,
        )
        result.append(cluster_obj)

    # Sort so most recurring faults appear first
    result.sort(key=lambda r: r.occurrence_count, reverse=True)
    return result


def get_fleet_recurring_leaderboard(
    chroma_client = None,
    min_occurrences: int = 1,
) -> List[dict]:
    """
    Scans all 4 machines in the fleet and compiles the recurring-fault leaderboard.
    Used for the Day 5 executive fleet dashboard.
    """
    fleet_machines = ["M-01", "M-02", "M-03", "M-04"]
    all_clusters: List[RecurringFaultCluster] = []

    for mid in fleet_machines:
        clusters = detect_recurring_faults(mid, chroma_client=chroma_client)
        all_clusters.extend(clusters)

    # Filter and sort by recurrence count
    filtered = [c for c in all_clusters if c.occurrence_count >= min_occurrences]
    filtered.sort(key=lambda c: (c.occurrence_count, c.severity == "critical"), reverse=True)

    leaderboard = []
    for rank, cluster in enumerate(filtered, start=1):
        leaderboard.append({
            "rank": rank,
            "machine_id": cluster.machine_id,
            "pattern_name": cluster.pattern_name,
            "failure_code": cluster.failure_code,
            "occurrence_count": cluster.occurrence_count,
            "severity": cluster.severity,
            "longest_lasting_fix": cluster.longest_lasting_fix,
            "summary_insight": cluster.summary_insight,
            "ticket_ids": cluster.ticket_ids,
        })

    return leaderboard


def match_symptom_recurrence(
    machine_id: str,
    symptom_text: str,
    similarity_threshold: float = 0.70,
    chroma_client = None,
) -> Optional[dict]:
    """
    Live match check: when a technician submits a symptom in chat or resolver pipeline,
    checks if this machine has previously experienced this exact recurring fault.

    Returns diagnostic advice dict if match found, else None.
    """
    client = chroma_client or get_chroma_client()
    try:
        col = get_tier2_collection(machine_id, client=client)
        res = col.query(
            query_texts=[symptom_text],
            n_results=3,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        print(f"[recurring_faults] Live match query error: {e}")
        return None

    if not res or not res.get("documents") or not res["documents"][0]:
        return None

    best_doc = res["documents"][0][0]
    best_meta = res["metadatas"][0][0] if res.get("metadatas") else {}
    distances = res["distances"][0] if res.get("distances") else [1.0]
    best_dist = distances[0]

    # In Chroma cosine distance: sim = 1.0 - dist
    similarity = max(0.0, 1.0 - best_dist) if best_dist <= 2.0 else 0.0

    if similarity >= similarity_threshold:
        prob = _extract_field(best_doc, "Problem") or best_meta.get("failure_code", "Known Fault")
        rem = _extract_field(best_doc, "Remedy / Corrective Action") or _extract_field(best_doc, "Resolution Summary")

        # Check total recurrences of this pattern
        clusters = detect_recurring_faults(machine_id, chroma_client=client)
        matching_cluster = next((c for c in clusters if c.failure_code == best_meta.get("failure_code")), None)
        count = matching_cluster.occurrence_count if matching_cluster else 1
        longest_fix = matching_cluster.longest_lasting_fix if matching_cluster else rem

        return {
            "matched": True,
            "machine_id": machine_id,
            "pattern_name": prob,
            "failure_code": best_meta.get("failure_code"),
            "similarity": round(similarity, 3),
            "occurrence_count": count,
            "longest_lasting_fix": longest_fix,
            "guidance": (
                f"⚠️ RECURRING FAULT PATTERN DETECTED: This issue has occurred {count} time{'s' if count != 1 else ''} "
                f"on {machine_id}. Historical repair logs indicate the longest-lasting fix was: {longest_fix}"
            ),
        }

    return None
