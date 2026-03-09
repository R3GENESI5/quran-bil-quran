# القرآن بالقرآن — Quran bil-Quran

A digital Mufharis (concordance) that connects Quranic verses through their Arabic roots. Click any word to discover every other verse in the Quran sharing the same root — the Quran explaining itself.

**[Live App](https://quran-bil-quran.netlify.app)** · **[Dataset on HuggingFace](https://huggingface.co/datasets/iqrossed/quran-bil-quran)**

## How It Works

1. **Read** — Browse the Quran sequentially, surah by surah
2. **Click** — Tap any word to reveal its trilateral Arabic root
3. **Connect** — See every other verse where that root appears (digital Mufharis)
4. **Explore** — Discover semantic families: groups of roots with shared meaning (e.g., خلق/برأ/فطر = "creation")

## Dataset

Three interconnected layers built from morphological analysis:

| Layer | File | Description |
|-------|------|-------------|
| Root Graph | `roots.jsonl` | 1,231 roots with occurrences, English meanings (Lane's Lexicon) |
| Semantic Families | `families.jsonl` | 35 families grouping synonymous roots |
| Convergence Map | `convergence.jsonl` | 5,710 verses mapped to their roots and families |

### Key Stats

- **1,231** unique roots (appearing in 2+ verses)
- **44,298** total verse occurrences
- **35** semantic families (creation, knowledge, guidance, mercy, etc.)
- **4,717** cross-family convergence points
- **98.6%** roots with English meanings from Lane's Lexicon

## Project Structure

```
src/
  quran_loader.py      # Downloads Quran text + morphology from APIs
  root_graph.py        # Builds root → verse index (digital Mufharis)
  root_families.py     # 35 semantic root families
  build_dataset.py     # Main pipeline: builds roots/families/convergence JSONL
  export_for_web.py    # Converts dataset to optimized JSON for the web app

app/                   # Static web app (deployed to Netlify)
  index.html
  css/style.css
  js/app.js

hf_dataset/            # HuggingFace dataset card
  README.md
```

## Build

```bash
# Install dependencies
pip install requests tqdm huggingface_hub

# Build dataset (downloads data on first run)
python src/build_dataset.py

# Export for web app
python src/export_for_web.py

# Serve locally
cd app && python -m http.server 8080
```

## Sources

- **Verse text**: [Quran.com API](https://quran.com) (Uthmani script)
- **Morphology**: [Quranic Arabic Corpus](https://github.com/mustafa0x/quran-morphology) (root/lemma/POS per word)
- **Root meanings**: [Lane's Lexicon dataset](https://github.com/aliozdenisik/quran-arabic-roots-lane-lexicon)
- **Semantic families**: Curated from classical Arabic lexicography (Lane's Lexicon, Maqayis al-Lugha)

## License

MIT
