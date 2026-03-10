# القرآن بالقرآن — Quran bil-Quran

A digital Mufharis (concordance) that lets the Quran explain itself. Click any word to discover every other verse sharing the same trilateral Arabic root — then trace how roots cluster into 35 semantic families, read classical tafsir from 11 scholars in 3 languages, and explore a force-directed thematic map.

**[Live App →](https://r3genesi5.github.io/quran-bil-quran/)** · **[Dataset on HuggingFace](https://huggingface.co/datasets/iqrossed/quran-bil-quran)**

---

## How It Works

### Reader (index.html)

1. **Read** — Browse all 114 surahs with full Uthmani Arabic text. Toggle Sahih International English translation, word-by-word hover meanings, or Latin transliteration. Adjust text scale (4 levels) and switch between light/dark mode
2. **Click any word** — A side panel reveals the word's trilateral root, its Lane's Lexicon meaning, Raghib al-Isfahani's classical definition (*Mufradat*), synonym distinctions (*Furuq*), semantic family membership, co-occurring roots, and every verse sharing that root
3. **Search roots** — The ⊕ search bar finds roots by Arabic letters, English meaning, or Buckwalter transliteration. Switch between **Roots** mode (1,651 entries) and **Furuq** mode (synonym distinctions)
4. **See the themes** — Colored dots under each verse show which of 6 macro-groups are present. A collapsible bar under each surah title shows the top semantic families and a computed insight with the dominant thematic register and distinctive families
5. **Read tafsir** — Click any verse number to expand inline tafsir. 11 tafsir sources available: 7 Arabic (API), 2 Urdu (pre-downloaded), 2 English (API) — switchable via dropdown

### Thematic Map (themes.html)

A D3.js force-directed edge bundling (FDEB) diagram visualizing how the 35 semantic families connect:

- **Chord layout** — families arranged in a circle, edges encode co-occurrence strength
- **Bundling slider** — adjust edge attraction to reveal natural thematic clusters
- **Per-surah filter** — see how family connections shift across individual surahs
- **Click-to-lock** — click a node to isolate its connections; click a connection in the detail panel to focus on a specific edge pair
- **Thematic summary** — auto-generated dominant register and strongest bridges for the selected surah

---

## Datasets

### Core Data

| File | Size | Description |
|------|------|-------------|
| `roots_index.json` | 740 KB | **1,651 roots** — Buckwalter transliteration, Lane's Lexicon meaning, frequency, verse list, and semantic family assignment |
| `families.json` | 28 KB | **35 semantic families** — groups of synonymous/related roots (e.g., خلق/برأ/فطر/صور = "creation"), with Arabic name and English meaning |
| `verses_text.json` | 1.4 MB | **6,236 verses** — full Uthmani Arabic text, keyed `"surah:ayah"` |
| `surah_list.json` | 17 KB | **114 surahs** — number, Arabic/English names, verse count, revelation type |
| `mufradat.json` | 787 KB | **Mufradat al-Quran** — classical vocabulary entries (Raghib al-Isfahani), root explanations and cited verses |
| `furuq.json` | 449 KB | **Furuq Lughawiyyah** — linguistic distinctions between near-synonym roots (e.g., خشية vs خوف) |

### Per-Surah Morphology

| Directory | Files | Description |
|-----------|-------|-------------|
| `surahs/` | 114 JSON | Word-level morphology per surah — each word has Arabic text (`t`), verse key (`v`), and root (`r`) |

### Translation Data

| File | Size | Description |
|------|------|-------------|
| `translations/en.sahih.json` | 925 KB | **Sahih International** English — 6,236 verse-level translations, keyed `"1:1": "text…"` |
| `translations/wbw.en.json` | 1.1 MB | **Word-by-word** English — per-word meanings keyed `"1:1": ["In (the) name", "of Allah", …]` |
| `translations/transliteration.json` | 1.0 MB | **Latin transliteration** — 6,236 verse-level romanized text |

### Pre-downloaded Tafsir

| Directory | Surah files | Size | Description |
|-----------|-------------|------|-------------|
| `tafsirs/bayan-ul-quran/` | 114 | 8.2 MB | **Bayan ul-Quran** — Urdu tafsir, verse-keyed HTML |
| `tafsirs/ibn-kathir-ur/` | 114 | 19 MB | **Ibn Kathir (Urdu)** — Urdu translation of the classical tafsir |

### HuggingFace Dataset (JSONL format for research)

| Layer | File | Records |
|-------|------|---------|
| Root Graph | `roots.jsonl` | 1,651 roots with occurrences and Lane's Lexicon meanings |
| Semantic Families | `families.jsonl` | 35 families grouping synonymous roots |
| Convergence Map | `convergence.jsonl` | 6,214 verses mapped to their roots and families |

---

## Thematic Inference Pipeline

No LLM is used. All thematic analysis is pure computation from the root-family graph:

### Step 1: Build verse → family map
Each of the 1,651 roots belongs to one of 35 semantic families (via `fam` field in `roots_index.json`). At init, `buildVerseFamilies()` iterates every root, and for each verse that root appears in, adds its family to that verse's family set. Result: **6,214 of 6,236 verses (99.6%)** have at least one themed root.

### Step 2: Aggregate into 6 macro-groups
The 35 families are mapped to 6 macro-groups:

| Group | Arabic | Families |
|-------|--------|----------|
| **Theology** | الإلهيات | creation, knowledge, guidance, revelation, prophets, covenant, divine_names, lordship |
| **Ethics** | الأخلاق | patience, gratitude, repentance, righteousness, corruption, justice, charity |
| **Eschatology** | الآخرة | afterlife, reward_punishment, time |
| **Nature** | الطبيعة | earth_sky, water_rain, light_dark, animals |
| **Human** | الإنسان | body, speech, emotion, seeing_hearing, provision |
| **Society** | المجتمع | community, warfare, family, trade, authority, travel |

### Step 3: Compute per-surah insight
For each surah, `renderSurahInsight()`:
1. Counts **unique verses** per macro-group (using Sets to avoid double-counting when a verse has multiple families in the same group)
2. Identifies the **dominant group** (highest verse coverage percentage)
3. Computes **distinctiveness** for each family: `surah_rate / quran_wide_rate`. Families with ratio > 1.5× and ≥ 3 occurrences are surfaced as "distinctive"

Example output for Al-Baqarah:
> **السمة الغالبة: الإلهيات** — Primary register: Theology — 73% of verses
> المميّز: الطهارة والتزكية (×3.6) · المال والتجارة (×3.1) · الحيوان والدواب (×2.4)

### Step 4: Per-verse thematic dots
Each verse gets colored dots (max 6) representing which macro-groups are present. One dot per group, using CSS custom properties `--group-0` through `--group-5` that auto-adapt to dark mode.

### Step 5: FDEB visualization (themes.html)
A D3.js force-directed edge bundling diagram arranges all 35 families in a circle. Edge thickness encodes co-occurrence strength (how many verses share both families). Bundling is controlled by a slider — edges attract toward nearby nodes, revealing natural clusters. Click-to-lock interaction lets you isolate a single family's connections or a specific edge pair.

---

## Tafsir

Click any verse number (①②③…) to expand an inline tafsir block. 11 sources available across 3 languages, switchable via dropdown:

### Arabic (live from quran.com API)

| ID | Name | Author |
|----|------|--------|
| 16 | **التفسير الميسّر** (default) | Muyassar — concise modern Arabic |
| 14 | **ابن كثير** | Ibn Kathir (d. 1373) — classical hadith-based |
| 91 | **السعدي** | Al-Sa'di (d. 1956) — concise classical |
| 94 | **البغوي** | Al-Baghawi (d. 1122) — traditional |
| 15 | **الطبري** | Al-Tabari (d. 923) — foundational classical |
| 90 | **القرطبي** | Al-Qurtubi (d. 1273) — jurisprudence-focused |
| 93 | **الوسيط — الطنطاوي** | Tantawi — modern comprehensive |

### Urdu (pre-downloaded, offline)

| Directory | Name |
|-----------|------|
| `bayan-ul-quran` | **بیان القرآن** — Ashraf Ali Thanawi |
| `ibn-kathir-ur` | **ابن کثیر اردو** — Urdu translation of Ibn Kathir |

### English (live from quran.com API)

| ID | Name |
|----|------|
| 169 | **Ibn Kathir (English)** |
| 168 | **Ma'ariful Qur'an** |

Tafsir responses are cached client-side per `tafsirId:verseKey` to minimize API calls. Pre-downloaded tafsirs load instantly from static JSON.

---

## Classical Lexicography

Two classical Arabic sources power the root-click panel:

**Mufradat al-Quran (المفردات في غريب القرآن)** — Raghib al-Isfahani's (d. ~1108) vocabulary of Quranic Arabic. When a root is clicked, its Mufradat entry shows the root's core meaning, semantic range, and cited Quranic verses.

**Furuq Lughawiyyah (الفروق اللغوية)** — Abu Hilal al-Askari's (d. ~1005) treatise on near-synonym distinctions. When a clicked root has known synonyms (e.g., خشية/خوف — "fear"), the Furuq panel explains the precise semantic difference between them. The search bar's Furuq mode lets you browse all distinction entries directly.

---

## Project Structure

```
src/
  quran_loader.py          # Downloads Quran text + morphology from APIs
  root_graph.py            # Builds root → verse index (digital Mufharis)
  root_families.py         # 35 semantic root families
  build_dataset.py         # Main pipeline: roots/families/convergence JSONL
  export_for_web.py        # Converts dataset to optimized JSON for web app
  download_translations.py # Fetches Sahih International + WBW from quran.com
  tafsir_fetcher.py        # Downloads complete tafsir texts from quran.com API
  parse_classical.py       # Parses Mufradat + Furuq classical sources

app/                       # Static web app (GitHub Pages)
  index.html               # Reader page
  themes.html              # FDEB chord diagram (self-contained)
  css/style.css            # Shared styles (light + dark mode)
  js/app.js                # Reader logic, thematic computation, translation
  data/
    roots_index.json       # Root glossary (1,651 roots)
    families.json          # 35 semantic families
    verses_text.json       # Full Quran text (Uthmani)
    surah_list.json        # 114 surah metadata
    mufradat.json          # Classical vocabulary (Raghib)
    furuq.json             # Synonym distinctions (Abu Hilal)
    surahs/                # Per-surah JSON (word-level morphology)
    tafsirs/               # Pre-downloaded Urdu tafsirs
    translations/
      en.sahih.json        # Sahih International English
      wbw.en.json          # Word-by-word English
      transliteration.json # Latin transliteration

hf_dataset/                # HuggingFace dataset card
  README.md
```

## Build

```bash
# Install dependencies
pip install requests tqdm huggingface_hub

# Build dataset from APIs (downloads on first run)
python src/build_dataset.py

# Export optimized JSON for web app
python src/export_for_web.py

# Download English translations (one-time)
python src/download_translations.py

# Download Urdu tafsirs (one-time)
python src/tafsir_fetcher.py

# Serve locally
cd app && python -m http.server 8080
```

## Key Stats

- **1,651** unique trilateral roots (all with Lane's Lexicon meanings)
- **6,236** verses with full Arabic text
- **44,718** total root-verse occurrences
- **35** semantic families across **6** macro-groups
- **6,214** verses (99.6%) with at least one themed root
- **11** tafsir sources in 3 languages (Arabic, Urdu, English)

## Sources

- **Verse text**: [Quran.com API](https://quran.com) — Uthmani script
- **Morphology**: [Quranic Arabic Corpus](https://github.com/mustafa0x/quran-morphology) — root/lemma/POS per word
- **Root meanings**: [Lane's Lexicon dataset](https://github.com/aliozdenisik/quran-arabic-roots-lane-lexicon)
- **Semantic families**: Curated from classical Arabic lexicography (Lane's Lexicon, Maqayis al-Lugha)
- **Mufradat**: Raghib al-Isfahani, *al-Mufradat fi Gharib al-Quran*
- **Furuq**: Abu Hilal al-Askari, *al-Furuq al-Lughawiyyah*
- **Tafsir (Arabic)**: Live from [quran.com API](https://api.quran.com/api/v4) (7 classical scholars)
- **Tafsir (Urdu)**: Pre-downloaded from quran.com API (Bayan ul-Quran, Ibn Kathir Urdu)
- **Tafsir (English)**: Live from quran.com API (Ibn Kathir English, Ma'ariful Qur'an)
- **Translation**: Sahih International + word-by-word via quran.com API (pre-downloaded)

## License

MIT
