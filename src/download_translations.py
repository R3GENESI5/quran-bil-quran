"""
Download Sahih International translation + word-by-word from quran.com API.
Outputs:
  app/data/translations/en.sahih.json   — { "1:1": "In the name of ...", ... }
  app/data/translations/wbw.en.json     — { "1:1": ["In", "the name", ...], ... }
"""
import json, re, time
from urllib.request import urlopen, Request
from pathlib import Path

API = "https://api.quran.com/api/v4"
TRANSLATION_ID = 20  # Sahih International
OUT_DIR = Path(__file__).resolve().parent.parent / "app" / "data" / "translations"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SURAH_VERSES = [
    7,286,200,176,120,165,206,75,129,109,123,111,43,52,99,128,111,110,98,135,
    112,78,118,64,77,227,93,88,69,60,34,30,73,54,45,83,182,88,75,85,54,53,89,
    59,37,35,38,29,18,45,60,49,62,55,78,96,29,22,24,13,14,11,11,18,12,12,30,
    52,52,44,28,28,20,56,40,31,50,40,46,42,29,19,36,25,22,17,19,26,30,20,15,
    21,11,8,8,19,5,8,8,11,11,8,3,9,5,4,7,3,6,3,5,4,5,6
]

headers = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) QuranBilQuran/1.0",
}

def fetch_json(url):
    req = Request(url, headers=headers)
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def download_translations():
    """Translations endpoint returns ordered array without verse_key.
    We generate keys from chapter number + 1-based index."""
    trans = {}
    for ch in range(1, 115):
        url = f"{API}/quran/translations/{TRANSLATION_ID}?chapter_number={ch}"
        data = fetch_json(url)
        verses = data.get("translations", [])
        for i, t in enumerate(verses, 1):
            vk = f"{ch}:{i}"
            text = t["text"]
            # Strip <sup> footnotes and any remaining HTML
            text = re.sub(r'<sup[^>]*>.*?</sup>', '', text)
            text = re.sub(r'<[^>]+>', '', text).strip()
            trans[vk] = text
        print(f"  [trans] Surah {ch}/114 — {len(verses)} verses")
        time.sleep(0.3)

    out = OUT_DIR / "en.sahih.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(trans, f, ensure_ascii=False, separators=(",", ":"))
    print(f"\n✓ Saved {len(trans)} translations → {out} ({out.stat().st_size // 1024} KB)")
    return trans


def download_wbw():
    """WBW endpoint returns verse_key on each verse object."""
    wbw = {}
    for ch in range(1, 115):
        total_verses = SURAH_VERSES[ch - 1]
        page = 1
        fetched = 0
        while fetched < total_verses:
            url = (f"{API}/verses/by_chapter/{ch}?language=en&words=true"
                   f"&word_fields=translation&per_page=50&page={page}")
            data = fetch_json(url)
            for v in data.get("verses", []):
                vk = v["verse_key"]
                words = []
                for w in v.get("words", []):
                    # Skip end-of-ayah markers
                    if w.get("char_type_name") == "end":
                        continue
                    tr = w.get("translation", {})
                    text = tr.get("text", "") if isinstance(tr, dict) else str(tr)
                    words.append(text)
                wbw[vk] = words
                fetched += 1
            page += 1
            time.sleep(0.3)
        print(f"  [wbw] Surah {ch}/114 — {fetched} verses")

    out = OUT_DIR / "wbw.en.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(wbw, f, ensure_ascii=False, separators=(",", ":"))
    print(f"\n✓ Saved {len(wbw)} WBW entries → {out} ({out.stat().st_size // 1024} KB)")
    return wbw


if __name__ == "__main__":
    print("═══ Downloading Sahih International translations ═══")
    download_translations()
    print("\n═══ Downloading word-by-word data ═══")
    download_wbw()
    print("\n✓ All done!")
