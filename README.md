# القرآن بالقرآن — Quran bil-Quran

A digital Mufharis (concordance) that lets the Quran explain itself. Click any word to discover every other verse sharing the same trilateral Arabic root — then see how roots cluster into semantic families, how tafsir scholars interpreted each ayah, and what thematic register dominates each surah.

**[Live App →](https://r3genesi5.github.io/quran-bil-quran/)** · **[Dataset on HuggingFace](https://huggingface.co/datasets/iqrossed/quran-bil-quran)**

---

## How It Works

1. **Read** — Browse the Quran surah by surah, with Sahih International English translation and word-by-word hover tooltips
2. **Click any word** — Reveal its trilateral Arabic root, Lane's Lexicon meaning, and every other verse where that root appears
3. **See the themes** — Colored dots under each verse show which of 6 macro-groups (Theology, Ethics, Eschatology, Nature, Human, Society) are present
4. **Read the insight** — A computed summary under each surah title shows its dominant thematic register and distinctive families
5. **Explore the map** — Force-directed edge bundling (FDEB) chord diagram visualizes how 35 semantic families connect across the entire Quran
6. **Read tafsir** — Click any verse number to load classical Arabic tafsir from 5 scholars, switchable via dropdown

---

## Datasets

### Core Data (built from morphological analysis)

| File | Size | Description |
|------|------|-------------|
| `roots_index.json` | 575 KB | **1,231 roots** — each with Buckwalter transliteration, English meaning (Lane's Lexicon), frequency, verse list, and `fam` field mapping to semantic families |
| `families.json` | 9 KB | **35 semantic families** — groups of synonymous roots (e.g., خلق/برأ/فطر/صور = "creation"), with Arabic name and English meaning |
| `verses_text.json` | 1.4 MB | **6,236 verses** — full Uthmani Arabic text, keyed by `surah:ayah` |
| `surah_list.json` | 17 KB | **114 surahs** — number, Arabic/English names, verse count, revelation type |
| `mufradat.json` | 787 KB | **Mufradat al-Quran** — classical vocabulary entries (Raghib al-Isfahani), with root explanations and cited verses |
| `furuq.json` | 449 KB | **Furuq Lughawiyyah** — linguistic distinctions between near-synonym roots (e.g., خشية vs خوف) |

### Translation Data (pre-downloaded from quran.com API)

| File | Size | Description |
|------|------|-------------|
| `en.sahih.json` | 925 KB | **Sahih International** English translation — 6,236 verse-level translations, keyed `"1:1": "text..."` |
| `wbw.en.json` | 1.1 MB | **Word-by-word** English — 6,236 entries, keyed `"1:1": ["In (the) name", "of Allah", ...]` mapping each Arabic word to its English meaning |

### HuggingFace Dataset (JSONL format for research)

| Layer | File | Records |
|-------|------|---------|
| Root Graph | `roots.jsonl` | 1,231 roots with occurrences and Lane's Lexicon meanings |
| Semantic Families | `families.jsonl` | 35 families grouping synonymous roots |
| Convergence Map | `convergence.jsonl` | 5,710 verses mapped to their roots and families |

---

## Thematic Inference Pipeline

No LLM is used. All thematic analysis is pure computation from the root-family graph:

### Step 1: Build verse → family map
Each of the 1,231 roots optionally belongs to one of 35 semantic families (via `fam` field in `roots_index.json`). At init, `buildVerseFamilies()` iterates every root, and for each verse that root appears in, adds its family to that verse's family set. Result: **5,710 of 6,236 verses (91%)** have at least one themed root.

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
A D3.js force-directed edge bundling diagram arranges all 35 families in a circle. Edge thickness encodes co-occurrence strength (how many verses share both families). Bundling is controlled by a slider — edges attract toward nearby nodes, revealing natural clusters. Can be filtered per-surah.

---

## Tafsir

Click any verse number (①②③...) to expand an inline tafsir block. Five classical Arabic tafsir are available, switchable via dropdown — all fetched live from the [quran.com API](https://api.quran.com/api/v4):

| ID | Name | Author |
|----|------|--------|
| 16 | **التفسير الميسّر** (default) | Muyassar — concise modern Arabic |
| 14 | **ابن كثير** | Ibn Kathir (d. 1373) — classical hadith-based |
| 91 | **السعدي** | Al-Sa'di (d. 1956) — concise classical |
| 90 | **البغوي** | Al-Baghawi (d. 1122) — traditional |
| 93 | **الوسيط — الطنطاوي** | Tantawi — modern comprehensive |

Tafsir responses are cached client-side per `tafsirId:verseKey` to minimize API calls.

---

## Classical Lexicography

Two classical Arabic sources power the root-click panel:

**Mufradat al-Quran (المفردات في غريب القرآن)** — Raghib al-Isfahani's (d. ~1108) vocabulary of Quranic Arabic. When a root is clicked, its Mufradat entry shows the root's core meaning, semantic range, and cited Quranic verses.

**Furuq Lughawiyyah (الفروق اللغوية)** — Abu Hilal al-Askari's (d. ~1005) treatise on near-synonym distinctions. When a clicked root has known synonyms (e.g., خشية/خوف — "fear"), the Furuq panel explains the precise semantic difference between them.

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

app/                       # Static web app (GitHub Pages)
  index.html               # Reader page
  themes.html              # FDEB chord diagram (self-contained)
  css/style.css            # Shared styles (light + dark mode)
  js/app.js                # Reader logic, thematic computation, translation
  data/
    roots_index.json       # Root glossary (1,231 roots)
    families.json          # 35 semantic families
    verses_text.json       # Full Quran text (Uthmani)
    surah_list.json        # 114 surah metadata
    mufradat.json          # Classical vocabulary (Raghib)
    furuq.json             # Synonym distinctions (Abu Hilal)
    translations/
      en.sahih.json        # Sahih International English
      wbw.en.json          # Word-by-word English
    surahs/                # Per-surah JSON (word-level morphology)

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

# Serve locally
cd app && python -m http.server 8080
```

## Key Stats

- **1,231** unique trilateral roots (appearing in 2+ verses)
- **6,236** verses with full Arabic text
- **44,298** total root-verse occurrences
- **35** semantic families across **6** macro-groups
- **5,710** verses (91%) with at least one themed root
- **4,717** cross-family convergence points
- **98.6%** roots with English meanings from Lane's Lexicon

## Sources

- **Verse text**: [Quran.com API](https://quran.com) — Uthmani script
- **Morphology**: [Quranic Arabic Corpus](https://github.com/mustafa0x/quran-morphology) — root/lemma/POS per word
- **Root meanings**: [Lane's Lexicon dataset](https://github.com/aliozdenisik/quran-arabic-roots-lane-lexicon)
- **Semantic families**: Curated from classical Arabic lexicography (Lane's Lexicon, Maqayis al-Lugha)
- **Mufradat**: Raghib al-Isfahani, *al-Mufradat fi Gharib al-Quran*
- **Furuq**: Abu Hilal al-Askari, *al-Furuq al-Lughawiyyah*
- **Tafsir**: Live from [quran.com API](https://api.quran.com/api/v4) (Muyassar, Ibn Kathir, Al-Sa'di, Al-Baghawi, Tantawi)
- **Translation**: Sahih International via quran.com API (pre-downloaded as static JSON)

## License

MIT
