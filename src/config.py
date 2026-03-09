"""Configuration for the Quran bil-Quran pipeline."""

import os

# Directories
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_PROCESSED = os.path.join(PROJECT_ROOT, "data", "processed")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# Quran.com API
QURAN_API_BASE = "https://api.quran.com/api/v4"

# Available Arabic tafsirs on Quran.com API
TAFSIRS = {
    14: {"name": "Tafsir Ibn Kathir", "slug": "ar-tafsir-ibn-kathir", "author": "Ibn Kathir"},
    15: {"name": "Tafsir al-Tabari", "slug": "ar-tafsir-al-tabari", "author": "al-Tabari"},
    16: {"name": "Tafsir Muyassar", "slug": "ar-tafsir-muyassar", "author": "Muyassar"},
    90: {"name": "Al-Qurtubi", "slug": "ar-tafseer-al-qurtubi", "author": "al-Qurtubi"},
    91: {"name": "Al-Sa'di", "slug": "ar-tafseer-al-saddi", "author": "al-Sadi"},
    93: {"name": "Al-Wasit (Tantawi)", "slug": "ar-tafsir-al-wasit", "author": "Tantawi"},
    94: {"name": "Al-Baghawi", "slug": "ar-tafsir-al-baghawi", "author": "al-Baghawi"},
}

# Quran structure
TOTAL_SURAHS = 114

# Verse matching
MIN_MATCH_WORDS = 3  # Minimum words for a citation to be matchable
MATCH_THRESHOLD = 0.6  # Fuzzy match threshold (0-1)

# Connection categories (for LLM classification)
CATEGORIES = [
    "Siyaqi",    # Contextual/situational
    "Bayani",    # Clarification/explanation
    "Lughawi",   # Linguistic/lexical
    "Mawdu'i",   # Thematic
    "Sababi",    # Causal/reason-based
    "Qisasi",    # Narrative/story-based
]
