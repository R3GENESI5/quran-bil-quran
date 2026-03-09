---
license: mit
task_categories:
  - text-classification
  - feature-extraction
language:
  - ar
  - en
tags:
  - quran
  - arabic
  - linguistics
  - root-analysis
  - semantic-families
  - concordance
  - mufharis
pretty_name: "Quran bil-Quran: Root-Based Verse Connections"
size_categories:
  - 1K<n<10K
---

# Quran bil-Quran: Root-Based Verse Connections

A linguistic dataset connecting Quranic verses through their Arabic roots — a digital Mufharis (concordance) with semantic family layers.

## Dataset Structure

Three interconnected layers:

### 1. `roots.jsonl` — Root Graph (1,231 entries)
Each Arabic root that appears in 2+ verses, with all its occurrences and English meanings from Lane's Lexicon.

```json
{
  "root": "رحم",
  "root_buckwalter": "rHm",
  "meaning_en": "The root رحم (rHm) primarily means to have mercy...",
  "semantic_field": "",
  "frequency": 313,
  "verse_keys": ["1:1", "1:3", "2:37", ...],
  "occurrences": [
    {
      "verse_key": "1:1",
      "verse_text": "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
      "word_forms": ["ٱلرَّحْمَـٰنِ", "ٱلرَّحِيمِ"],
      "lemmas": ["رَحِيم", "رَحْمَـٰن"]
    }
  ]
}
```

### 2. `families.jsonl` — Semantic Root Families (35 families)
Roots grouped by shared meaning (e.g., خلق/برأ/فطر = "creation"). Includes convergence verses where multiple family roots appear together.

```json
{
  "family_id": "creation",
  "family_name": "Creating, originating, fashioning, bringing into being",
  "family_name_ar": "الخلق والإيجاد",
  "roots": ["خلق", "برأ", "فطر", "صور", "جعل", "بدع", "نشأ", "صنع", "كون"],
  "convergence_count": 42,
  "convergence_verses": [...]
}
```

### 3. `convergence.jsonl` — Verse Convergence Map (5,710 entries)
Each verse mapped to its roots and semantic families. Cross-family convergence points are thematic epicenters.

```json
{
  "verse_key": "73:20",
  "verse_text": "...",
  "roots": ["علم", "قوم", "ليل", ...],
  "root_count": 38,
  "families": {"fighting": ["قتل"], "mercy": ["غفر"], ...},
  "family_count": 17,
  "cross_family": true
}
```

## Key Stats

| Metric | Value |
|--------|-------|
| Unique roots (2+ occurrences) | 1,231 |
| Total verse occurrences | 44,298 |
| Roots with English meanings | 1,214 (98.6%) |
| Semantic families | 35 |
| Cross-family convergence points | 4,717 |
| Top convergence verse | 73:20 (17 families, 38 roots) |

## 35 Semantic Families

creation, knowledge, guidance, provision, punishment, mercy, worship, revelation, life_death, earth_sky, fear_hope, speech_communication, truth_falsehood, justice, light_darkness, seeing_hearing, water, fighting, wealth, patience_gratitude, heart_soul, prophets_messengers, covenant_promise, time, movement_journey, paradise, hellfire, family_kinship, deception_hypocrisy, pride_humility, repentance_return, purity, plants_agriculture, animals, body

## Sources

- **Verse text**: Quran.com API (Uthmani script)
- **Morphology**: [Quranic Arabic Corpus](https://github.com/mustafa0x/quran-morphology) (root/lemma/POS per word)
- **Root meanings**: [Lane's Lexicon dataset](https://github.com/aliozdenisik/quran-arabic-roots-lane-lexicon)
- **Semantic families**: Curated from classical Arabic lexicography (Lane's Lexicon, Maqayis al-Lugha)

## Methodology

1. Parse morphological data to extract root for every word in every verse
2. Build reverse index: root → all verses it appears in (digital Mufharis)
3. Add English meanings from Lane's Lexicon (98.6% coverage)
4. Group semantically related roots into 35 families
5. Map convergence points where multiple roots/families intersect in a single verse

## Use Cases

- **Quran bil-Quran study**: Find how the Quran explains itself through repeated roots
- **Thematic analysis**: Discover verses that sit at the intersection of multiple themes
- **NLP research**: Pre-built Arabic root graph for downstream tasks
- **Concordance apps**: Build digital Mufharis tools
