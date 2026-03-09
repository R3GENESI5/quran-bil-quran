"""Download and cache the full Quran text + morphology data."""

import json
import os
import re
import time
import requests
from config import QURAN_API_BASE, DATA_RAW, DATA_PROCESSED, TOTAL_SURAHS


def download_quran_text(force=False):
    """Download all verses from Quran.com API and cache locally."""
    cache_path = os.path.join(DATA_PROCESSED, "quran_verses.json")
    if os.path.exists(cache_path) and not force:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    print("Downloading Quran text from API...")
    all_verses = {}

    for surah in range(1, TOTAL_SURAHS + 1):
        page = 1
        while True:
            url = (
                f"{QURAN_API_BASE}/verses/by_chapter/{surah}"
                f"?language=ar&words=false&fields=text_uthmani,verse_key"
                f"&per_page=50&page={page}"
            )
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            for v in data["verses"]:
                all_verses[v["verse_key"]] = v["text_uthmani"]

            pagination = data.get("pagination", {})
            if page >= pagination.get("total_pages", 1):
                break
            page += 1
            time.sleep(0.15)  # Rate limiting

        if surah % 10 == 0:
            print(f"  Surah {surah}/{TOTAL_SURAHS} done ({len(all_verses)} verses)")

    os.makedirs(DATA_PROCESSED, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(all_verses, f, ensure_ascii=False, indent=2)

    print(f"Downloaded {len(all_verses)} verses total.")
    return all_verses


def load_morphology():
    """Load and parse the Quranic Arabic Corpus morphology data.

    Returns dict: verse_key -> list of {word, root, lemma, pos}
    """
    morph_path = os.path.join(DATA_RAW, "quran-morphology.txt")
    if not os.path.exists(morph_path):
        raise FileNotFoundError(f"Morphology file not found: {morph_path}")

    cache_path = os.path.join(DATA_PROCESSED, "morphology.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    print("Parsing morphology data...")
    verse_morphology = {}

    with open(morph_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 4:
                continue

            location = parts[0]  # e.g. "1:1:1:1"
            word = parts[1]
            pos = parts[2]
            features = parts[3]

            # Parse location -> verse_key
            loc_parts = location.split(":")
            if len(loc_parts) >= 2:
                verse_key = f"{loc_parts[0]}:{loc_parts[1]}"

            # Extract root and lemma from features
            root = ""
            lemma = ""
            for feat in features.split("|"):
                if feat.startswith("ROOT:"):
                    root = feat[5:]
                elif feat.startswith("LEM:"):
                    lemma = feat[4:]

            if verse_key not in verse_morphology:
                verse_morphology[verse_key] = []

            if root:  # Only include words with roots (content words)
                verse_morphology[verse_key].append({
                    "word": word,
                    "root": root,
                    "lemma": lemma,
                    "pos": pos,
                })

    os.makedirs(DATA_PROCESSED, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(verse_morphology, f, ensure_ascii=False, indent=2)

    print(f"Parsed morphology for {len(verse_morphology)} verses.")
    return verse_morphology


def build_root_index(morphology):
    """Build reverse index: root -> set of verse_keys.

    This is essentially a digital Mufharis.
    """
    cache_path = os.path.join(DATA_PROCESSED, "root_index.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    print("Building root index (digital Mufharis)...")
    root_index = {}

    for verse_key, words in morphology.items():
        for w in words:
            root = w["root"]
            if root not in root_index:
                root_index[root] = []
            if verse_key not in root_index[root]:
                root_index[root].append(verse_key)

    os.makedirs(DATA_PROCESSED, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(root_index, f, ensure_ascii=False, indent=2)

    total_roots = len(root_index)
    rare_roots = sum(1 for v in root_index.values() if len(v) <= 5)
    print(f"Root index: {total_roots} unique roots, {rare_roots} rare roots (<=5 occurrences)")
    return root_index


def load_root_meanings():
    """Load root meanings from Lane's Lexicon dataset.

    Returns dict: root -> {summary_en, definition_en, semantic_field, ...}
    """
    path = os.path.join(DATA_PROCESSED, "root_meanings.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Root meanings not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    lookup = {}
    for entry in data["roots"]:
        lookup[entry["root"]] = {
            "summary_en": entry.get("summary_en", ""),
            "definition_en": entry.get("definition_en", ""),
            "semantic_field": entry.get("semantic_field", ""),
            "root_buckwalter": entry.get("root_buckwalter", ""),
        }

    print(f"Loaded meanings for {len(lookup)} roots")
    return lookup


if __name__ == "__main__":
    verses = download_quran_text()
    morph = load_morphology()
    root_idx = build_root_index(morph)
    meanings = load_root_meanings()
    print(f"Sample meaning: {list(meanings.items())[0]}")
