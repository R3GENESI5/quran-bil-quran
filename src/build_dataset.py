"""Build the final Quran bil-Quran dataset.

Three layers, one dataset:
  1. Root Graph — each root links to every verse it appears in
  2. Root Families — semantically related roots form super-clusters
  3. Convergence Map — verses where multiple family roots converge
"""

import json
import os
from collections import defaultdict
from config import OUTPUT_DIR
from quran_loader import download_quran_text, load_morphology, build_root_index, load_root_meanings
from root_graph import build_root_graph
from root_families import SEMANTIC_FAMILIES, validate_families, build_family_graph


def build_convergence_map(family_graph, morphology, root_index, verses):
    """Build a verse-centric convergence map.

    For each verse, list all roots present and which families they belong to.
    Verses with roots from multiple families are cross-family convergence points.
    """
    print("\nBuilding convergence map...")

    # Reverse map: root -> family_id
    root_to_family = {}
    for fg in family_graph:
        for root in fg["roots"]:
            if root not in root_to_family:
                root_to_family[root] = []
            root_to_family[root].append(fg["family_id"])

    # For each verse, collect roots and their families
    verse_map = {}
    for vk, words in morphology.items():
        roots_in_verse = list(set(w["root"] for w in words if w["root"]))
        if not roots_in_verse:
            continue

        families_in_verse = defaultdict(list)
        for root in roots_in_verse:
            for fam_id in root_to_family.get(root, []):
                families_in_verse[fam_id].append(root)

        if not families_in_verse:
            continue

        verse_map[vk] = {
            "verse_key": vk,
            "verse_text": verses.get(vk, ""),
            "roots": roots_in_verse,
            "root_count": len(roots_in_verse),
            "families": {
                fam_id: sorted(set(roots))
                for fam_id, roots in families_in_verse.items()
            },
            "family_count": len(families_in_verse),
            "cross_family": len(families_in_verse) >= 2,
        }

    # Sort by family count descending
    convergence_list = sorted(
        verse_map.values(),
        key=lambda x: (-x["family_count"], -x["root_count"]),
    )

    cross_count = sum(1 for v in convergence_list if v["cross_family"])
    print(f"  {len(convergence_list)} verses mapped")
    print(f"  {cross_count} cross-family convergence points")

    return convergence_list


def build_full_dataset():
    """Build and save the complete dataset."""
    print("=" * 60)
    print("QURAN BIL-QURAN DATASET BUILDER")
    print("=" * 60)

    # Load foundations
    print("\n[1/5] Loading Quran text...")
    verses = download_quran_text()

    print("\n[2/6] Loading morphology...")
    morph = load_morphology()
    root_idx = build_root_index(morph)

    print("\n[3/6] Loading root meanings...")
    meanings = load_root_meanings()

    # Layer 1: Root graph
    print("\n[4/6] Building root graph...")
    root_graph = build_root_graph(morph, verses, root_idx, meanings)

    # Layer 2: Root families
    print("\n[5/6] Building root families...")
    validated = validate_families(root_idx)
    family_graph = build_family_graph(validated, root_idx, verses, morph)

    # Layer 3: Convergence map
    print("\n[6/6] Building convergence map...")
    convergence = build_convergence_map(family_graph, morph, root_idx, verses)

    # Save all three layers
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Root graph
    path1 = os.path.join(OUTPUT_DIR, "roots.jsonl")
    with open(path1, "w", encoding="utf-8") as f:
        for entry in root_graph:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Root families
    path2 = os.path.join(OUTPUT_DIR, "families.jsonl")
    with open(path2, "w", encoding="utf-8") as f:
        for entry in family_graph:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Convergence map
    path3 = os.path.join(OUTPUT_DIR, "convergence.jsonl")
    with open(path3, "w", encoding="utf-8") as f:
        for entry in convergence:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Summary stats
    print("\n" + "=" * 60)
    print("DATASET COMPLETE")
    print("=" * 60)
    print(f"\n  roots.jsonl       — {len(root_graph):,} roots")
    print(f"  families.jsonl    — {len(family_graph):,} semantic families")
    print(f"  convergence.jsonl — {len(convergence):,} verse mappings")

    cross = sum(1 for v in convergence if v["cross_family"])
    print(f"\n  Cross-family convergence points: {cross:,}")
    print(f"  Total verse occurrences: {sum(e['frequency'] for e in root_graph):,}")

    # Top convergence points
    print("\n  TOP 10 CONVERGENCE VERSES (most families):")
    for v in convergence[:10]:
        fams = ", ".join(v["families"].keys())
        print(f"    {v['verse_key']} ({v['family_count']} families, {v['root_count']} roots)")
        print(f"      Families: {fams}")
        print(f"      {v['verse_text'][:70]}...")

    print(f"\n  Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    build_full_dataset()
