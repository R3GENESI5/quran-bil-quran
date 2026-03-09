"""Fetch tafsir text from Quran.com API."""

import json
import os
import re
import time
import requests
from config import QURAN_API_BASE, DATA_RAW, TAFSIRS, TOTAL_SURAHS


def fetch_tafsir_by_chapter(tafsir_id, surah_num):
    """Fetch all tafsir entries for a surah.

    Returns list of {verse_key, text} dicts.
    """
    url = f"{QURAN_API_BASE}/tafsirs/{tafsir_id}/by_chapter/{surah_num}"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    entries = []
    for item in data.get("tafsirs", []):
        entries.append({
            "verse_key": item["verse_key"],
            "text": item["text"],
        })
    return entries


def fetch_full_tafsir(tafsir_id, force=False):
    """Download complete tafsir and cache as JSON.

    Args:
        tafsir_id: numeric ID from TAFSIRS config
        force: re-download even if cached
    """
    info = TAFSIRS[tafsir_id]
    cache_path = os.path.join(DATA_RAW, f"tafsir-{info['slug']}.json")

    if os.path.exists(cache_path) and not force:
        print(f"Loading cached tafsir: {info['name']}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    print(f"Downloading tafsir: {info['name']} (id={tafsir_id})...")
    all_entries = []

    for surah in range(1, TOTAL_SURAHS + 1):
        try:
            entries = fetch_tafsir_by_chapter(tafsir_id, surah)
            all_entries.extend(entries)
        except Exception as e:
            print(f"  ERROR surah {surah}: {e}")

        if surah % 10 == 0:
            print(f"  Surah {surah}/{TOTAL_SURAHS} ({len(all_entries)} entries)")

        time.sleep(0.2)  # Rate limiting

    os.makedirs(DATA_RAW, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_entries)} tafsir entries for {info['name']}")
    return all_entries


if __name__ == "__main__":
    # Test with a single surah
    entries = fetch_tafsir_by_chapter(15, 1)  # Tabari, Al-Fatiha
    for e in entries:
        text_preview = re.sub(r"<[^>]+>", "", e["text"])[:100]
        print(f"{e['verse_key']}: {text_preview}...")
