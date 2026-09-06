"""Historical context, original-language roots, and public-domain commentary.

Coverage is CURATED, not complete — these are hand-checked entries for passages
the demo corpus covers. `has_lexicon()` tells the client the truth so the UI can
say "no lexical data for this verse" instead of implying the silence is meaning.

To make this complete, ingest a Strong's-tagged text (STEPBible TAHOT/TAGNT,
CC-BY) keyed by the same Ref addresses. That is a data job, not a code job — the
shape below already matches what a tagged import would produce.
"""
from __future__ import annotations

# key = Ref.label
ENTRIES: dict[str, dict] = {
    "Philippians 4:6-7": {
        "context": "Written from Roman custody around AD 62. Paul is chained to a rotating guard and does not know whether his trial ends in release or execution — the letter's repeated command to rejoice is issued from that position, not from safety. Philippi was a Roman colony of retired soldiers, so the military vocabulary in verse 7 would have landed on its intended audience.",
        "commentary": {
            "source": "Matthew Henry, Commentary on the Whole Bible (1710, public domain)",
            "text": "The peace of God is that peace which God gives, and it passeth all understanding: it is what cannot be fully comprehended, and it keeps the heart as with a garrison.",
        },
        "lemmas": [
            {"word": "μεριμνάω", "translit": "merimnaō", "strongs": "G3309", "gloss": "to be anxious",
             "note": "Likely from merizō, 'to divide'. The picture is a mind pulled into parts — not fear, but fragmentation."},
            {"word": "εἰρήνη", "translit": "eirēnē", "strongs": "G1515", "gloss": "peace",
             "note": "Carries the freight of Hebrew shalom — wholeness and repair, not merely the absence of conflict."},
            {"word": "φρουρέω", "translit": "phroureō", "strongs": "G5432", "gloss": "will guard",
             "note": "A garrison term: to post a military sentry. The peace is not a feeling here; it is a soldier at the gate."},
        ],
    },
    "1 Peter 5:6-7": {
        "context": "Addressed to scattered believers in Asia Minor facing social hostility rather than state persecution — shunning, slander, lost work. Verses 6 and 7 are one sentence in Greek: the casting is how the humbling is done, not a separate instruction.",
        "lemmas": [
            {"word": "ἐπιρίπτω", "translit": "epiriptō", "strongs": "G1977", "gloss": "cast upon",
             "note": "Used in Luke 19:35 of throwing cloaks onto the colt — a decisive heave off yourself onto something else."},
            {"word": "μέριμνα", "translit": "merimna", "strongs": "G3308", "gloss": "anxiety, care",
             "note": "The noun behind Paul's verb in Philippians 4:6. Same root, same divided mind."},
        ],
    },
    "Matthew 6:25-27": {
        "context": "From the Sermon on the Mount, spoken to a subsistence-agrarian crowd for whom a failed harvest was a genuine survival threat. The argument is not that the worry is irrational — it is that it is ineffective, and that the hearer has misjudged their own worth.",
        "lemmas": [
            {"word": "μεριμνάω", "translit": "merimnaō", "strongs": "G3309", "gloss": "to worry",
             "note": "The same verb Paul commands against in Philippians 4:6 — a deliberate echo."},
            {"word": "ἡλικία", "translit": "hēlikia", "strongs": "G2244", "gloss": "stature / lifespan",
             "note": "Ambiguous in Greek: height or age. KJV chose 'cubit unto his stature'; modern versions read it as lifespan."},
        ],
    },
    "Jeremiah 29:11": {
        "context": "The most quoted and most decontextualised verse in the Bible. It is a letter to deportees in Babylon, and the surrounding verses set the terms: the promise is collective, not individual, and it arrives after seventy years (v.10). Verse 5 tells the same audience to build houses and plant gardens — i.e. this is a promise for a generation that will mostly die in exile.",
        "commentary": {
            "source": "Jamieson-Fausset-Brown, Commentary Critical and Explanatory (1871, public domain)",
            "text": "An expected end — literally, 'a latter end and expectation'; that is, the end which you hope for, and which shall not disappoint you.",
        },
        "lemmas": [
            {"word": "מַחֲשָׁבָה", "translit": "machashabah", "strongs": "H4284", "gloss": "thoughts, plans",
             "note": "From chashab, 'to weave' or 'to reckon'. Deliberate design, not a passing intention."},
            {"word": "תִּקְוָה", "translit": "tiqvah", "strongs": "H8615", "gloss": "hope",
             "note": "Concretely a cord or rope — the same word for Rahab's scarlet line in Joshua 2:18. Hope as something you hold onto."},
        ],
    },
    "Romans 15:13": {
        "context": "The closing benediction of Paul's argument to a Roman church split between Jewish and Gentile believers. 'Hope' here is the payoff of eleven chapters of argument, not a mood — it names the confidence that the two groups share one future.",
        "lemmas": [
            {"word": "ἐλπίς", "translit": "elpis", "strongs": "G1680", "gloss": "hope",
             "note": "Confident expectation of a specific outcome. Unlike English 'hope', it carries no implication of doubt."},
            {"word": "περισσεύω", "translit": "perisseuō", "strongs": "G4052", "gloss": "to overflow",
             "note": "Surplus language — more than the container holds. Used of the leftover baskets after the feeding of the five thousand."},
        ],
    },
    "Romans 8:28": {
        "context": "Sits inside a passage about suffering and groaning creation (vv. 18-27), which is what 'all things' refers back to. The verse is a claim about trajectory under pressure, and the manuscripts differ on whether God or 'all things' is the subject — hence the split between modern versions and the KJV.",
        "lemmas": [
            {"word": "συνεργέω", "translit": "synergeō", "strongs": "G4903", "gloss": "to work together",
             "note": "Root of English 'synergy'. Whether God is the subject is a genuine textual question, not a translation preference."},
            {"word": "πρόθεσις", "translit": "prothesis", "strongs": "G4286", "gloss": "purpose",
             "note": "Literally 'a setting forth' — the same word used for the showbread set out in the temple. Purpose as something placed deliberately."},
        ],
    },
    "Ephesians 2:10": {
        "context": "Immediately follows the letter's sharpest denial that works save anyone (vv. 8-9). The sequence matters: the works are the output of the making, not the price of it. Ephesus was a craft city — the temple of Artemis supported a large guild of metalworkers — so 'workmanship' was shop-floor vocabulary.",
        "lemmas": [
            {"word": "ποίημα", "translit": "poiēma", "strongs": "G4161", "gloss": "workmanship",
             "note": "The root of English 'poem'. A made thing, valued for what it is rather than what it produces."},
        ],
    },
    "Genesis 6:8": {
        "context": "The first occurrence of chen in the Hebrew Bible, placed as the hinge of the flood narrative — one clause of favour against a chapter of judgment. KJV renders it 'grace'; most modern versions say 'favour', which is why word-study across translations can quietly mislead.",
        "lemmas": [
            {"word": "חֵן", "translit": "chen", "strongs": "H2580", "gloss": "favour, grace",
             "note": "Relational and often asymmetric — what a superior extends to an inferior. It is found, not earned, but the OT rarely makes it a technical term."},
        ],
    },
    "Exodus 34:6": {
        "context": "God's self-description, given immediately after the golden calf — i.e. the definitive OT statement of grace is delivered to a people who have just broken the covenant. Quoted or alluded to more than a dozen times across the OT; it functions as Israel's creed.",
        "lemmas": [
            {"word": "חֶסֶד", "translit": "chesed", "strongs": "H2617", "gloss": "loyal love",
             "note": "The heavyweight OT grace word — covenant loyalty that persists when the other party has forfeited it. Notoriously hard to translate; 'lovingkindness' was coined for it."},
            {"word": "חַנּוּן", "translit": "channun", "strongs": "H2587", "gloss": "gracious",
             "note": "Same root as chen. Used only of God in the Hebrew Bible."},
        ],
    },
    "Ephesians 2:8-9": {
        "context": "Where charis becomes a technical term. Paul is writing into a Greco-Roman patronage culture in which a gift created a debt and a public obligation to the giver — verse 9 exists to cut that expectation off, which is a sharper move in its own setting than it reads as now.",
        "lemmas": [
            {"word": "χάρις", "translit": "charis", "strongs": "G5485", "gloss": "grace",
             "note": "Ordinary Greek for a favour or benefaction. The NT keeps the word and removes the reciprocity that made it work."},
        ],
    },
}

def get(label: str) -> dict:
    return ENTRIES.get(label, {})

def has_lexicon(label: str) -> bool:
    return bool(ENTRIES.get(label, {}).get("lemmas"))

COVERAGE = len(ENTRIES)
