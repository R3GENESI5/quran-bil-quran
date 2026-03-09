"""Root-centric Quran connection graph.

The root is the connection. Each root links to every verse it appears in.
Verses are connected THROUGH roots, not directly.
"""

import json
import os
from collections import defaultdict
from config import DATA_PROCESSED, OUTPUT_DIR


def build_root_graph(morphology, verses, root_index, root_meanings=None):
    """Build root-centric graph.

    Each root entry contains:
    - The root itself
    - Meaning (from Lane's Lexicon)
    - All verses where it appears
    - Word forms it takes in each verse
    - Frequency stats
    """
    print("Building root-centric graph...")
    root_meanings = root_meanings or {}

    graph = []

    for root, verse_keys in sorted(root_index.items(), key=lambda x: len(x[1])):
        if len(verse_keys) < 2:
            continue  # Skip hapax legomena (single occurrence)

        # Collect word forms per verse
        occurrences = []
        for vk in verse_keys:
            words_in_verse = [
                w for w in morphology.get(vk, [])
                if w["root"] == root
            ]
            forms = [w["word"] for w in words_in_verse]
            lemmas = list(set(w["lemma"] for w in words_in_verse if w["lemma"]))

            occurrences.append({
                "verse_key": vk,
                "verse_text": verses.get(vk, ""),
                "word_forms": forms,
                "lemmas": lemmas,
            })

        meaning = root_meanings.get(root, {})
        entry = {
            "root": root,
            "root_buckwalter": meaning.get("root_buckwalter", ""),
            "meaning_en": meaning.get("summary_en", ""),
            "semantic_field": meaning.get("semantic_field", ""),
            "frequency": len(verse_keys),
            "verse_keys": verse_keys,
            "occurrences": occurrences,
        }

        graph.append(entry)

    # Sort by frequency ascending (rarest roots first = strongest connections)
    graph.sort(key=lambda x: x["frequency"])

    print(f"Built graph: {len(graph)} roots connecting {sum(e['frequency'] for e in graph)} verse occurrences")
    return graph


def save_root_graph(graph, filename="root_graph.jsonl"):
    """Save as JSONL."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        for entry in graph:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Saved to {path}")
    return path


def print_stats(graph):
    """Print distribution stats."""
    print("\n=== ROOT GRAPH STATS ===")
    print(f"Total roots (with 2+ occurrences): {len(graph)}")

    buckets = {"2-3": 0, "4-5": 0, "6-10": 0, "11-25": 0, "26-50": 0, "51-100": 0, "100+": 0}
    for e in graph:
        f = e["frequency"]
        if f <= 3: buckets["2-3"] += 1
        elif f <= 5: buckets["4-5"] += 1
        elif f <= 10: buckets["6-10"] += 1
        elif f <= 25: buckets["11-25"] += 1
        elif f <= 50: buckets["26-50"] += 1
        elif f <= 100: buckets["51-100"] += 1
        else: buckets["100+"] += 1

    print("\nFrequency distribution:")
    for bucket, count in buckets.items():
        bar = "█" * (count // 5)
        print(f"  {bucket:>6} verses: {count:>4} roots  {bar}")

    # Most connected roots
    print("\n=== TOP 10 MOST CONNECTED ROOTS ===")
    for e in sorted(graph, key=lambda x: -x["frequency"])[:10]:
        sample_forms = set()
        for occ in e["occurrences"][:5]:
            sample_forms.update(occ["word_forms"])
        forms_str = ", ".join(list(sample_forms)[:4])
        print(f"  {e['root']} ({e['frequency']} verses) — forms: {forms_str}")

    # Rarest meaningful roots (exactly 2 occurrences)
    print("\n=== SAMPLE RARE ROOTS (2 occurrences = strongest links) ===")
    count = 0
    for e in graph:
        if e["frequency"] == 2:
            v1 = e["occurrences"][0]
            v2 = e["occurrences"][1]
            print(f"\n  Root: {e['root']}")
            print(f"    {v1['verse_key']}: {v1['verse_text'][:70]}...")
            print(f"    Forms: {', '.join(v1['word_forms'])}")
            print(f"    {v2['verse_key']}: {v2['verse_text'][:70]}...")
            print(f"    Forms: {', '.join(v2['word_forms'])}")
            count += 1
            if count >= 5:
                break


if __name__ == "__main__":
    from quran_loader import download_quran_text, load_morphology, build_root_index

    verses = download_quran_text()
    morph = load_morphology()
    root_idx = build_root_index(morph)

    graph = build_root_graph(morph, verses, root_idx)
    print_stats(graph)
    save_root_graph(graph)
