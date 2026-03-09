"""Extract verse-to-verse connections from tafsir and morphology data."""

import json
import os
import re
from collections import defaultdict
from config import DATA_PROCESSED, OUTPUT_DIR, TAFSIRS
from verse_matcher import VerseMatcher, extract_citations_from_tafsir, normalize_arabic


class ConnectionExtractor:
    """Extracts Quran bil-Quran connections from multiple sources."""

    def __init__(self, verses, morphology=None, root_index=None):
        self.verses = verses
        self.matcher = VerseMatcher(verses)
        self.morphology = morphology or {}
        self.root_index = root_index or {}

    def extract_from_tafsir(self, tafsir_entries, tafsir_id):
        """Extract connections from tafsir text.

        For each verse's tafsir, find cited verses via text matching.
        """
        tafsir_info = TAFSIRS.get(tafsir_id, {"name": f"tafsir-{tafsir_id}", "author": "unknown"})
        connections = []
        total = len(tafsir_entries)

        for i, entry in enumerate(tafsir_entries):
            verse_key = entry["verse_key"]
            html_text = entry["text"]

            # Extract cited fragments
            citations = extract_citations_from_tafsir(html_text)

            for citation in citations:
                # Try to match this citation to a verse
                matches = self.matcher.find_matches(
                    citation,
                    source_verse=verse_key,
                    min_words=3,
                    top_k=1,
                )

                for matched_key, score in matches:
                    if score < 0.4:
                        continue

                    # Extract surrounding context from tafsir
                    context = self._extract_context(html_text, citation)

                    connections.append({
                        "source": "tafsir",
                        "tafsir": tafsir_info["name"],
                        "tafsir_author": tafsir_info["author"],
                        "ayah_key": verse_key,
                        "ayah_text": self.verses.get(verse_key, ""),
                        "connected_key": matched_key,
                        "connected_text": self.verses.get(matched_key, ""),
                        "citation_text": citation,
                        "match_score": round(score, 3),
                        "context": context,
                    })

            if (i + 1) % 500 == 0:
                print(f"  Processed {i+1}/{total} verses, found {len(connections)} connections")

        return connections

    def extract_from_roots(self, max_root_frequency=10, min_shared_roots=2):
        """Extract connections based on shared rare roots (Mufharis approach).

        Two verses are connected if they share multiple rare roots.
        Rare = root appears in <= max_root_frequency verses.
        """
        print(f"Extracting root-based connections (max_freq={max_root_frequency}, min_shared={min_shared_roots})...")

        # Get rare roots
        rare_roots = {
            root: verses
            for root, verses in self.root_index.items()
            if 2 <= len(verses) <= max_root_frequency
        }
        print(f"  {len(rare_roots)} rare roots (frequency 2-{max_root_frequency})")

        # Build verse pair -> shared roots mapping
        pair_roots = defaultdict(set)
        for root, verse_keys in rare_roots.items():
            for i, v1 in enumerate(verse_keys):
                for v2 in verse_keys[i+1:]:
                    # Canonical ordering
                    pair = tuple(sorted([v1, v2], key=self._verse_sort_key))
                    pair_roots[pair].add(root)

        # Filter pairs with enough shared roots
        connections = []
        for (v1, v2), shared in pair_roots.items():
            if len(shared) >= min_shared_roots:
                connections.append({
                    "source": "root_analysis",
                    "tafsir": "Quranic Arabic Corpus",
                    "tafsir_author": "Corpus Linguistics",
                    "ayah_key": v1,
                    "ayah_text": self.verses.get(v1, ""),
                    "connected_key": v2,
                    "connected_text": self.verses.get(v2, ""),
                    "shared_roots": sorted(list(shared)),
                    "num_shared_roots": len(shared),
                    "match_score": min(1.0, len(shared) / 5),  # Normalize
                })

        print(f"  Found {len(connections)} root-based connections")
        return connections

    def _extract_context(self, html_text, citation, context_chars=200):
        """Extract surrounding context from tafsir text around a citation."""
        clean = re.sub(r"<[^>]+>", "", html_text)
        norm_citation = normalize_arabic(citation)
        norm_clean = normalize_arabic(clean)

        idx = norm_clean.find(norm_citation)
        if idx == -1:
            return ""

        start = max(0, idx - context_chars)
        end = min(len(clean), idx + len(citation) + context_chars)
        return clean[start:end].strip()

    def _verse_sort_key(self, verse_key):
        """Sort key for verse references (1:1 < 1:2 < 2:1)."""
        parts = verse_key.split(":")
        return (int(parts[0]), int(parts[1]))


def save_connections(connections, filename):
    """Save connections as JSONL."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        for conn in connections:
            f.write(json.dumps(conn, ensure_ascii=False) + "\n")
    print(f"Saved {len(connections)} connections to {path}")


if __name__ == "__main__":
    print("Use run_pipeline.py to run the full extraction.")
