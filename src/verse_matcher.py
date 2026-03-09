"""Match Arabic text fragments to Quranic verse keys.

This is the core engine: given a fragment like "وكذلك جعلنا لكل نبي عدوا",
find the verse it belongs to (6:112).
"""

import re
import unicodedata


def normalize_arabic(text):
    """Normalize Arabic text for comparison.

    Removes diacritics (tashkeel), normalizes alef/hamza variants,
    removes tatweel, and collapses whitespace.
    """
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Remove diacritics (Arabic tashkeel: fatha, damma, kasra, shadda, sukun, etc.)
    # Unicode range for Arabic diacritics: U+064B to U+065F, U+0670
    diacritics = re.compile(r"[\u064B-\u065F\u0670\u06D6-\u06ED]")
    text = diacritics.sub("", text)

    # Normalize alef variants -> bare alef
    text = re.sub(r"[إأآٱ]", "ا", text)

    # Normalize taa marbuta -> haa
    text = text.replace("ة", "ه")

    # Normalize alef maqsura -> ya
    text = text.replace("ى", "ي")

    # Remove tatweel (kashida)
    text = text.replace("\u0640", "")

    # Remove non-Arabic characters except spaces
    text = re.sub(r"[^\u0600-\u06FF\s]", "", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


class VerseMatcher:
    """Matches Arabic text fragments to Quranic verses."""

    def __init__(self, verses):
        """
        Args:
            verses: dict of verse_key -> Arabic text (uthmani script)
        """
        self.verses = verses
        # Pre-normalize all verses for fast matching
        self.normalized = {}
        self.verse_words = {}
        for key, text in verses.items():
            norm = normalize_arabic(text)
            self.normalized[key] = norm
            self.verse_words[key] = norm.split()

    def find_matches(self, fragment, source_verse=None, min_words=3, top_k=3):
        """Find verses matching a text fragment.

        Args:
            fragment: Arabic text fragment to match
            source_verse: verse_key of the verse being explained (excluded from results)
            min_words: minimum words in fragment to attempt matching
            top_k: return top K matches

        Returns:
            List of (verse_key, score) tuples, sorted by score descending.
        """
        norm_frag = normalize_arabic(fragment)
        frag_words = norm_frag.split()

        if len(frag_words) < min_words:
            return []

        matches = []

        for key, norm_verse in self.normalized.items():
            # Skip the source verse itself
            if key == source_verse:
                continue

            score = self._score_match(frag_words, norm_verse, self.verse_words[key])
            if score > 0.3:
                matches.append((key, score))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:top_k]

    def _score_match(self, frag_words, norm_verse, verse_words):
        """Score how well a fragment matches a verse.

        Uses a combination of:
        1. Substring containment (exact match of normalized fragment in verse)
        2. Word overlap ratio (Jaccard-like)
        3. Consecutive word sequence matching
        """
        frag_str = " ".join(frag_words)

        # Exact substring match = perfect score
        if frag_str in norm_verse:
            # Score based on coverage: how much of the verse does the fragment cover?
            coverage = len(frag_str) / max(len(norm_verse), 1)
            return 0.8 + (0.2 * coverage)

        # Word overlap
        frag_set = set(frag_words)
        verse_set = set(verse_words)
        if not frag_set or not verse_set:
            return 0.0

        intersection = frag_set & verse_set
        if len(intersection) < 2:
            return 0.0

        # Jaccard-like score weighted toward fragment coverage
        frag_coverage = len(intersection) / len(frag_set)
        verse_coverage = len(intersection) / len(verse_set)

        # Find longest consecutive match
        max_consec = self._longest_consecutive(frag_words, verse_words)
        consec_score = max_consec / max(len(frag_words), 1)

        # Combined score
        score = (0.3 * frag_coverage) + (0.2 * verse_coverage) + (0.5 * consec_score)
        return score

    def _longest_consecutive(self, frag_words, verse_words):
        """Find length of longest consecutive word sequence from fragment in verse."""
        if not frag_words or not verse_words:
            return 0

        max_len = 0
        for i in range(len(verse_words)):
            j = 0
            k = i
            while j < len(frag_words) and k < len(verse_words):
                if frag_words[j] == verse_words[k]:
                    j += 1
                    k += 1
                else:
                    break
            max_len = max(max_len, j)
        return max_len


def extract_citations_from_tafsir(html_text):
    """Extract Quranic citations from tafsir HTML text.

    Quran.com tafsir format uses <span class="arabic qpc-hafs green">
    to wrap verse citations.

    Returns list of citation strings.
    """
    # Primary: extract from green spans (explicit verse citations)
    citations = re.findall(
        r'<span[^>]*class="[^"]*green[^"]*"[^>]*>\s*\(?(.*?)\)?\s*</span>',
        html_text,
        re.DOTALL,
    )

    # Clean HTML from within citations
    cleaned = []
    for c in citations:
        c = re.sub(r"<[^>]+>", "", c).strip()
        c = re.sub(r"^\(|\)$", "", c).strip()  # Remove surrounding parens
        if len(c) > 2:  # Skip single-character fragments
            cleaned.append(c)

    return cleaned


if __name__ == "__main__":
    # Quick test
    test_verses = {
        "1:1": "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
        "6:112": "وَكَذَٰلِكَ جَعَلْنَا لِكُلِّ نَبِىٍّ عَدُوًّا شَيَـٰطِينَ ٱلْإِنسِ وَٱلْجِنِّ",
        "96:1": "ٱقْرَأْ بِٱسْمِ رَبِّكَ ٱلَّذِى خَلَقَ",
        "11:41": "بِسْمِ ٱللَّهِ مَجْر۪ىٰهَا وَمُرْسَىٰهَآ",
    }

    matcher = VerseMatcher(test_verses)

    test_fragments = [
        "اقرأ باسم ربك الذي خلق",
        "وكذلك جعلنا لكل نبي عدوا شياطين الإنس والجن",
        "بسم الله مجراها ومرساها",
    ]

    for frag in test_fragments:
        matches = matcher.find_matches(frag, source_verse="1:1")
        print(f"\nFragment: {frag}")
        for key, score in matches:
            print(f"  -> {key}: {score:.3f} ({test_verses[key][:50]})")
