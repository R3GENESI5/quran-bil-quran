"""Semantic root families — roots with related meanings.

Roots that share meaning create a meta-connection layer.
If خلق and برأ are in the same family, their verse clusters merge
into a larger thematic web.
"""

import json
import os
from collections import defaultdict
from config import DATA_PROCESSED, OUTPUT_DIR


# ─── Curated Semantic Families ───────────────────────────────────────
# Each family: name -> list of roots that share the semantic field.
# Sourced from classical Arabic lexicography (Lane's Lexicon, Maqayis al-Lugha).
# Add/edit these as needed.

SEMANTIC_FAMILIES = {
    # ─── Original 20 families ─────────────────────────────────
    "creation": {
        "name_ar": "الخلق والإيجاد",
        "roots": ["خلق", "برأ", "فطر", "صور", "جعل", "بدع", "نشأ", "صنع", "كون"],
        "meaning": "Creating, originating, fashioning, bringing into being",
    },
    "knowledge": {
        "name_ar": "العلم والمعرفة",
        "roots": ["علم", "عرف", "فقه", "درك", "شعر", "حكم", "فهم", "بصر", "خبر"],
        "meaning": "Knowing, understanding, perceiving, wisdom",
    },
    "guidance": {
        "name_ar": "الهداية والضلال",
        "roots": ["هدي", "رشد", "ضلل", "غوي", "صرط", "سبل", "طرق", "نهج"],
        "meaning": "Guidance, misguidance, paths, ways",
    },
    "provision": {
        "name_ar": "الرزق والإنفاق",
        "roots": ["رزق", "نفق", "طعم", "أكل", "سقي", "شرب", "قوت", "متع"],
        "meaning": "Provision, sustenance, food, drink, spending",
    },
    "punishment": {
        "name_ar": "العذاب والعقوبة",
        "roots": ["عذب", "عقب", "نقم", "أخذ", "هلك", "دمر", "قصم", "صعق"],
        "meaning": "Punishment, retribution, destruction",
    },
    "mercy": {
        "name_ar": "الرحمة والمغفرة",
        "roots": ["رحم", "غفر", "عفو", "تيب", "صفح", "حلم", "رأف"],
        "meaning": "Mercy, forgiveness, pardon, forbearance",
    },
    "worship": {
        "name_ar": "العبادة والتقوى",
        "roots": ["عبد", "سجد", "ركع", "صلو", "صوم", "حجج", "ذكر", "سبح", "دعو"],
        "meaning": "Worship, prayer, fasting, remembrance, supplication",
    },
    "revelation": {
        "name_ar": "الوحي والكتاب",
        "roots": ["وحي", "نزل", "كتب", "قرأ", "تلو", "بين", "فصل"],
        "meaning": "Revelation, scripture, recitation, clarification",
    },
    "life_death": {
        "name_ar": "الحياة والموت",
        "roots": ["حيي", "موت", "بعث", "نشر", "قبر", "حشر", "قوم"],
        "meaning": "Life, death, resurrection, gathering",
    },
    "earth_sky": {
        "name_ar": "الأرض والسماء",
        "roots": ["أرض", "سمو", "جبل", "بحر", "نهر", "شمس", "قمر", "نجم", "فلك"],
        "meaning": "Earth, heavens, mountains, seas, celestial bodies",
    },
    "fear_hope": {
        "name_ar": "الخوف والرجاء",
        "roots": ["خوف", "خشي", "رهب", "وجل", "رجو", "طمع", "أمن"],
        "meaning": "Fear, awe, hope, security",
    },
    "speech_communication": {
        "name_ar": "القول والكلام",
        "roots": ["قول", "كلم", "نطق", "حدث", "خطب", "نبأ", "بشر", "نذر"],
        "meaning": "Speech, communication, glad tidings, warning",
    },
    "truth_falsehood": {
        "name_ar": "الحق والباطل",
        "roots": ["حقق", "صدق", "بطل", "كذب", "زور", "إفك", "ظنن"],
        "meaning": "Truth, falsehood, lying, conjecture",
    },
    "justice": {
        "name_ar": "العدل والظلم",
        "roots": ["عدل", "قسط", "ظلم", "بغي", "جور", "حكم", "وزن", "كيل"],
        "meaning": "Justice, equity, oppression, judgement, measure",
    },
    "light_darkness": {
        "name_ar": "النور والظلمة",
        "roots": ["نور", "ظلم", "ضوء", "سرج", "شهب", "لمع"],
        "meaning": "Light, darkness, illumination",
    },
    "seeing_hearing": {
        "name_ar": "البصر والسمع",
        "roots": ["بصر", "نظر", "رأي", "سمع", "أذن", "صمم", "عمي"],
        "meaning": "Seeing, hearing, blindness, deafness",
    },
    "water": {
        "name_ar": "الماء والمطر",
        "roots": ["مطر", "غيث", "ماء", "سقي", "نبع", "عين", "بئر", "نهر"],
        "meaning": "Water, rain, springs, rivers",
    },
    "fighting": {
        "name_ar": "القتال والجهاد",
        "roots": ["قتل", "جهد", "حرب", "غزو", "نصر", "فتح", "هزم"],
        "meaning": "Fighting, striving, war, victory, defeat",
    },
    "wealth": {
        "name_ar": "المال والتجارة",
        "roots": ["مول", "تجر", "ربح", "خسر", "بيع", "شري", "كنز", "ربو"],
        "meaning": "Wealth, trade, profit, loss, buying, selling",
    },
    "patience_gratitude": {
        "name_ar": "الصبر والشكر",
        "roots": ["صبر", "شكر", "حمد", "كفر", "جزع"],
        "meaning": "Patience, gratitude, praise, ingratitude",
    },
    # ─── New families ─────────────────────────────────────────
    "heart_soul": {
        "name_ar": "القلب والنفس",
        "roots": ["قلب", "نفس", "صدر", "لبب", "روح", "عقل"],
        "meaning": "Heart, soul, chest, intellect, spirit",
    },
    "prophets_messengers": {
        "name_ar": "الأنبياء والرسل",
        "roots": ["نبأ", "رسل", "وحي", "بعث", "صفو"],
        "meaning": "Prophets, messengers, revelation, mission, chosen",
    },
    "covenant_promise": {
        "name_ar": "العهد والميثاق",
        "roots": ["عهد", "عقد", "حلف", "نذر", "وعد", "يمن"],
        "meaning": "Covenant, oath, vow, promise, pledge",
    },
    "time": {
        "name_ar": "الزمان والأجل",
        "roots": ["يوم", "ليل", "نهر", "دهر", "عصر", "أجل", "أبد", "قرن"],
        "meaning": "Day, night, time, epoch, term, eternity",
    },
    "movement_journey": {
        "name_ar": "الحركة والسفر",
        "roots": ["مشي", "سير", "سفر", "هجر", "خرج", "دخل", "رجع", "أتي"],
        "meaning": "Walking, traveling, migration, entering, exiting, returning",
    },
    "paradise": {
        "name_ar": "الجنة والنعيم",
        "roots": ["جنن", "نعم", "خلد", "فوز", "فلح", "فرح"],
        "meaning": "Paradise, bliss, eternity, success, joy",
    },
    "hellfire": {
        "name_ar": "النار والجحيم",
        "roots": ["سعر", "جحم", "لظي", "حرق", "وقد", "حمم", "حطم"],
        "meaning": "Hellfire, blaze, burning, fuel, crushing fire",
    },
    "family_kinship": {
        "name_ar": "الأسرة والقرابة",
        "roots": ["أهل", "ولد", "أبو", "أمم", "أخو", "زوج"],
        "meaning": "Family, children, parents, kin, spouse",
    },
    "deception_hypocrisy": {
        "name_ar": "المكر والنفاق",
        "roots": ["مكر", "كيد", "خدع", "غرر", "نفق", "منن"],
        "meaning": "Plotting, scheming, deception, hypocrisy",
    },
    "pride_humility": {
        "name_ar": "الكبر والتواضع",
        "roots": ["كبر", "عظم", "خشع", "ذلل", "خضع"],
        "meaning": "Pride, arrogance, humility, submission",
    },
    "repentance_return": {
        "name_ar": "التوبة والإنابة",
        "roots": ["توب", "أوب", "رجع", "ندم"],
        "meaning": "Repentance, returning to God, regret",
    },
    "purity": {
        "name_ar": "الطهارة والتزكية",
        "roots": ["طهر", "زكو", "صفو", "غسل"],
        "meaning": "Purity, purification, cleansing, spiritual growth",
    },
    "plants_agriculture": {
        "name_ar": "النبات والزراعة",
        "roots": ["نبت", "زرع", "حبب", "شجر", "ثمر", "حرث", "جنن"],
        "meaning": "Plants, seeds, trees, fruits, cultivation, gardens",
    },
    "animals": {
        "name_ar": "الحيوان والدواب",
        "roots": ["بقر", "غنم", "خيل", "حمر", "طير", "حوت", "نمل", "نحل"],
        "meaning": "Cattle, sheep, horses, birds, fish, ants, bees",
    },
    "body": {
        "name_ar": "الجسد والأعضاء",
        "roots": ["يدي", "رجل", "وجه", "عين", "رأس", "جلد", "بطن", "ظهر"],
        "meaning": "Hands, feet, face, eyes, head, skin, body parts",
    },
}


def validate_families(root_index):
    """Check which roots from families actually exist in the Quran corpus."""
    print("Validating semantic families against corpus...")

    validated = {}
    for family_id, family in SEMANTIC_FAMILIES.items():
        present = [r for r in family["roots"] if r in root_index]
        missing = [r for r in family["roots"] if r not in root_index]

        if len(present) >= 2:
            validated[family_id] = {
                **family,
                "roots": present,
                "missing_roots": missing,
                "root_count": len(present),
            }

            if missing:
                print(f"  {family_id}: {len(present)} found, {len(missing)} missing ({', '.join(missing)})")

    print(f"Validated {len(validated)} families with 2+ roots in corpus")
    return validated


def build_family_graph(validated_families, root_index, verses, morphology):
    """Build the semantic family connection layer.

    For each family, collect all verse clusters from member roots
    and mark the family-level connections.
    """
    print("\nBuilding semantic family graph...")

    family_graph = []

    for family_id, family in validated_families.items():
        roots = family["roots"]

        # Collect all unique verses touched by this family
        all_verses = set()
        root_details = {}
        for root in roots:
            vkeys = root_index.get(root, [])
            all_verses.update(vkeys)
            root_details[root] = {
                "frequency": len(vkeys),
                "verse_keys": vkeys,
            }

        # Build occurrence map: which roots appear in which verses
        verse_root_map = defaultdict(list)
        for root in roots:
            for vk in root_index.get(root, []):
                # Get word forms
                forms = [
                    w["word"] for w in morphology.get(vk, [])
                    if w["root"] == root
                ]
                verse_root_map[vk].append({
                    "root": root,
                    "word_forms": forms,
                })

        # Find verses with multiple family roots (convergence points)
        convergence_verses = {
            vk: roots_info
            for vk, roots_info in verse_root_map.items()
            if len(roots_info) >= 2
        }

        entry = {
            "family_id": family_id,
            "family_name": family["meaning"],
            "family_name_ar": family["name_ar"],
            "roots": roots,
            "root_details": root_details,
            "total_verses": len(all_verses),
            "convergence_count": len(convergence_verses),
            "convergence_verses": [
                {
                    "verse_key": vk,
                    "verse_text": verses.get(vk, ""),
                    "roots_present": info,
                }
                for vk, info in sorted(
                    convergence_verses.items(),
                    key=lambda x: -len(x[1])
                )[:50]  # Cap at 50 examples
            ],
        }

        family_graph.append(entry)

    family_graph.sort(key=lambda x: -x["convergence_count"])

    print(f"Built {len(family_graph)} family entries")
    return family_graph


def save_family_graph(graph, filename="root_families.jsonl"):
    """Save as JSONL."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        for entry in graph:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Saved to {path}")
    return path


def print_family_stats(graph):
    """Display family overview."""
    print("\n=== SEMANTIC FAMILY OVERVIEW ===")
    for entry in graph:
        roots_str = " ".join(entry["roots"])
        print(f"\n  [{entry['family_id']}] {entry['family_name']}")
        print(f"    {entry['family_name_ar']}")
        print(f"    Roots: {roots_str}")
        print(f"    Verses: {entry['total_verses']} | Convergence points: {entry['convergence_count']}")

        # Show top convergence verse
        if entry["convergence_verses"]:
            top = entry["convergence_verses"][0]
            roots_in = [r["root"] for r in top["roots_present"]]
            print(f"    Best convergence: {top['verse_key']} ({', '.join(roots_in)})")
            print(f"      {top['verse_text'][:80]}...")


if __name__ == "__main__":
    from quran_loader import download_quran_text, load_morphology, build_root_index

    verses = download_quran_text()
    morph = load_morphology()
    root_idx = build_root_index(morph)

    validated = validate_families(root_idx)
    graph = build_family_graph(validated, root_idx, verses, morph)
    print_family_stats(graph)
    save_family_graph(graph)
