"""Export dataset to web-ready JSON for the Quran reader app."""

import json
import os
import requests
from collections import defaultdict
from config import DATA_RAW, DATA_PROCESSED, QURAN_API_BASE
from root_families import SEMANTIC_FAMILIES

APP_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "data")


def parse_word_roots():
    """Parse raw morphology to get root per word-position in each verse.

    Returns: {verse_key: {word_position(int): root_string}}
    """
    morph_path = os.path.join(DATA_RAW, "quran-morphology.txt")
    word_roots = defaultdict(dict)

    with open(morph_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 4:
                continue

            loc_parts = parts[0].split(":")
            if len(loc_parts) < 4:
                continue

            verse_key = f"{loc_parts[0]}:{loc_parts[1]}"
            word_pos = int(loc_parts[2])
            features = parts[3]

            root = ""
            for feat in features.split("|"):
                if feat.startswith("ROOT:"):
                    root = feat[5:]

            # Only keep first root found per word position (stem root)
            if root and word_pos not in word_roots[verse_key]:
                word_roots[verse_key][word_pos] = root

    print(f"  Word roots parsed for {len(word_roots)} verses")
    return dict(word_roots)


def fetch_surah_list():
    """Fetch surah names from Quran.com API."""
    cache_path = os.path.join(DATA_PROCESSED, "surah_list.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    print("  Fetching surah list from API...")
    url = f"{QURAN_API_BASE}/chapters?language=en"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    surahs = []
    for ch in data["chapters"]:
        surahs.append({
            "number": ch["id"],
            "name_ar": ch["name_arabic"],
            "name_en": ch["name_simple"],
            "name_translation": ch["translated_name"]["name"],
            "verses_count": ch["verses_count"],
            "revelation_place": ch["revelation_place"],
        })

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(surahs, f, ensure_ascii=False, indent=2)

    return surahs


def _is_pause_mark(token):
    """Check if a whitespace-separated token is a Uthmani pause/stop mark.

    These marks (ۛ ۚ ۙ ۖ ۗ ۘ ۜ ۩) appear as separate tokens in the Uthmani
    text but are NOT counted as word positions in the morphology corpus.
    Skipping them keeps position indices aligned.
    """
    return len(token) == 1 and token in "\u06D6\u06D7\u06D8\u06D9\u06DA\u06DB\u06DC\u06E9"


def export_surah_files(verses, word_roots):
    """Export per-surah JSON files with word-level root mapping."""
    surahs_dir = os.path.join(APP_DATA_DIR, "surahs")
    os.makedirs(surahs_dir, exist_ok=True)

    surah_verses = defaultdict(list)
    for vk, text in verses.items():
        surah_num = int(vk.split(":")[0])
        ayah_num = int(vk.split(":")[1])

        vk_roots = word_roots.get(vk, {})
        words = text.split()

        word_data = []
        morph_pos = 0  # position counter aligned with morphology corpus
        for word_text in words:
            if _is_pause_mark(word_text):
                # Pause marks are not in the morphology data — no position increment
                word_data.append({"t": word_text})
                continue
            morph_pos += 1
            root = vk_roots.get(morph_pos, None)
            entry = {"t": word_text}
            if root:
                entry["r"] = root
            word_data.append(entry)

        surah_verses[surah_num].append({
            "k": vk,
            "a": ayah_num,
            "words": word_data,
        })

    for surah_num in sorted(surah_verses.keys()):
        ayahs = sorted(surah_verses[surah_num], key=lambda x: x["a"])
        path = os.path.join(surahs_dir, f"{surah_num}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ayahs, f, ensure_ascii=False, separators=(",", ":"))

    print(f"  Exported {len(surah_verses)} surah files")


def export_root_index(root_index, root_meanings):
    """Export compact root index for instant lookups."""
    # Build root -> families mapping
    root_to_families = defaultdict(list)
    for fam_id, fam in SEMANTIC_FAMILIES.items():
        for root in fam["roots"]:
            root_to_families[root].append(fam_id)

    index = {}
    for root, verse_keys in root_index.items():
        if len(verse_keys) < 2:
            continue

        meaning = root_meanings.get(root, {})
        entry = {
            "b": meaning.get("root_buckwalter", ""),
            "m": meaning.get("summary_en", ""),
            "f": len(verse_keys),
            "v": verse_keys,
        }

        fams = root_to_families.get(root, [])
        if fams:
            entry["fam"] = fams

        index[root] = entry

    path = os.path.join(APP_DATA_DIR, "roots_index.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = os.path.getsize(path) / 1024
    print(f"  Root index: {len(index)} roots ({size_kb:.0f}KB)")


def export_families(root_index):
    """Export validated semantic families."""
    validated = {}
    for fam_id, fam in SEMANTIC_FAMILIES.items():
        present = [r for r in fam["roots"] if r in root_index and len(root_index[r]) >= 2]
        if len(present) >= 2:
            validated[fam_id] = {
                "name_ar": fam["name_ar"],
                "meaning": fam["meaning"],
                "roots": present,
            }

    path = os.path.join(APP_DATA_DIR, "families.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(validated, f, ensure_ascii=False, indent=2)

    print(f"  Families: {len(validated)}")


def export_verses_text(verses):
    """Export all verse texts as a compact lookup for root panel."""
    path = os.path.join(APP_DATA_DIR, "verses_text.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(verses, f, ensure_ascii=False, separators=(",", ":"))

    size_mb = os.path.getsize(path) / 1024 / 1024
    print(f"  Verses text: {len(verses)} verses ({size_mb:.1f}MB)")


def main():
    from quran_loader import download_quran_text, build_root_index, load_morphology, load_root_meanings

    print("=" * 50)
    print("EXPORTING FOR WEB APP")
    print("=" * 50)

    os.makedirs(APP_DATA_DIR, exist_ok=True)

    print("\n[1] Loading data...")
    verses = download_quran_text()
    morph = load_morphology()
    root_idx = build_root_index(morph)
    meanings = load_root_meanings()

    print("\n[2] Parsing word-level morphology...")
    word_roots = parse_word_roots()

    print("\n[3] Fetching surah list...")
    surah_list = fetch_surah_list()

    print("\n[4] Exporting...")
    # Surah list
    path = os.path.join(APP_DATA_DIR, "surah_list.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(surah_list, f, ensure_ascii=False)
    print(f"  Surah list: {len(surah_list)} surahs")

    export_surah_files(verses, word_roots)
    export_root_index(root_idx, meanings)
    export_families(root_idx)
    export_verses_text(verses)

    print(f"\nDone! Output: {APP_DATA_DIR}")


if __name__ == "__main__":
    main()
