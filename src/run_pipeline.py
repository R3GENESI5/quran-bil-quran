"""Main pipeline runner.

Layer 1 (Primary): Root-based connections from Quranic Arabic Corpus
Layer 2 (Secondary): Tafsir citation connections from Quran.com API
"""

import json
import os
import sys
import time
from config import DATA_PROCESSED, OUTPUT_DIR, TAFSIRS
from quran_loader import download_quran_text, load_morphology, build_root_index
from connection_extractor import ConnectionExtractor, save_connections
from tafsir_fetcher import fetch_full_tafsir


def run_layer1_roots(extractor, max_freq=10, min_shared=2):
    """Layer 1: Root-based connections (primary)."""
    print("\n" + "=" * 60)
    print("LAYER 1: Root-Based Connections (Primary)")
    print("=" * 60)

    connections = extractor.extract_from_roots(
        max_root_frequency=max_freq,
        min_shared_roots=min_shared,
    )

    save_connections(connections, "layer1_root_connections.jsonl")
    return connections


def run_layer2_tafsir(extractor, tafsir_ids=None):
    """Layer 2: Tafsir citation connections (secondary)."""
    print("\n" + "=" * 60)
    print("LAYER 2: Tafsir Citation Connections (Secondary)")
    print("=" * 60)

    if tafsir_ids is None:
        tafsir_ids = list(TAFSIRS.keys())

    all_connections = []

    for tid in tafsir_ids:
        info = TAFSIRS[tid]
        print(f"\nProcessing: {info['name']} (id={tid})")

        entries = fetch_full_tafsir(tid)
        connections = extractor.extract_from_tafsir(entries, tid)
        all_connections.extend(connections)

        slug = info["slug"]
        save_connections(connections, f"layer2_{slug}.jsonl")

    save_connections(all_connections, "layer2_all_tafsir_connections.jsonl")
    return all_connections


def merge_layers(root_conns, tafsir_conns):
    """Merge both layers into a unified dataset.

    Deduplicates and marks each connection with its source layers.
    """
    print("\n" + "=" * 60)
    print("MERGING LAYERS")
    print("=" * 60)

    # Index by verse pair
    merged = {}

    # Add root connections first (primary)
    for conn in root_conns:
        pair_key = f"{conn['ayah_key']}|{conn['connected_key']}"
        if pair_key not in merged:
            merged[pair_key] = {
                "ayah_key": conn["ayah_key"],
                "ayah_text": conn["ayah_text"],
                "connected_key": conn["connected_key"],
                "connected_text": conn["connected_text"],
                "layers": [],
                "shared_roots": conn.get("shared_roots", []),
                "num_shared_roots": conn.get("num_shared_roots", 0),
            }
        merged[pair_key]["layers"].append({
            "source": "root_analysis",
            "match_score": conn["match_score"],
            "shared_roots": conn.get("shared_roots", []),
        })

    # Add tafsir connections (secondary)
    for conn in tafsir_conns:
        pair_key = f"{conn['ayah_key']}|{conn['connected_key']}"
        reverse_key = f"{conn['connected_key']}|{conn['ayah_key']}"

        key = pair_key if pair_key in merged else reverse_key if reverse_key in merged else pair_key

        if key not in merged:
            merged[key] = {
                "ayah_key": conn["ayah_key"],
                "ayah_text": conn["ayah_text"],
                "connected_key": conn["connected_key"],
                "connected_text": conn["connected_text"],
                "layers": [],
                "shared_roots": [],
                "num_shared_roots": 0,
            }
        merged[key]["layers"].append({
            "source": "tafsir",
            "tafsir": conn.get("tafsir", ""),
            "tafsir_author": conn.get("tafsir_author", ""),
            "citation_text": conn.get("citation_text", ""),
            "context": conn.get("context", ""),
            "match_score": conn["match_score"],
        })

    # Convert to list and add metadata
    result = []
    for pair_key, data in merged.items():
        data["num_layers"] = len(set(l["source"] for l in data["layers"]))
        data["total_evidence"] = len(data["layers"])
        data["max_score"] = max(l["match_score"] for l in data["layers"])

        # Strength classification
        if data["num_layers"] >= 2:
            data["strength"] = "strong"  # Both layers agree
        elif data["total_evidence"] >= 3:
            data["strength"] = "moderate"
        else:
            data["strength"] = "weak"

        result.append(data)

    # Sort by evidence strength
    result.sort(key=lambda x: (-x["num_layers"], -x["total_evidence"], -x["max_score"]))

    save_connections(result, "quran_bil_quran_merged.jsonl")

    # Stats
    strong = sum(1 for r in result if r["strength"] == "strong")
    moderate = sum(1 for r in result if r["strength"] == "moderate")
    weak = sum(1 for r in result if r["strength"] == "weak")
    print(f"\nMerged: {len(result)} unique connections")
    print(f"  Strong (both layers): {strong}")
    print(f"  Moderate: {moderate}")
    print(f"  Weak: {weak}")

    return result


def main():
    print("QURAN BIL-QURAN CONNECTION PIPELINE")
    print("=" * 60)

    # Step 1: Load foundational data
    print("\nStep 1: Loading Quran text and morphology...")
    verses = download_quran_text()
    morphology = load_morphology()
    root_index = build_root_index(morphology)

    # Step 2: Initialize extractor
    extractor = ConnectionExtractor(verses, morphology, root_index)

    # Step 3: Layer 1 - Root connections (primary)
    root_conns = run_layer1_roots(extractor)

    # Step 4: Layer 2 - Tafsir connections (secondary)
    # Start with Tabari (id=15) as it's the most comprehensive
    tafsir_conns = run_layer2_tafsir(extractor, tafsir_ids=[15])

    # Step 5: Merge
    merged = merge_layers(root_conns, tafsir_conns)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
