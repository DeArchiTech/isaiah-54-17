"""Canonical scripture references — parsing, formatting, ordering.

A Ref is the atomic address in this system. Everything that crosses the API
boundary carries one, and anything claiming to be scripture must resolve to one.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, asdict

# Canonical order; also the alias source. Keys are canonical names.
BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges",
    "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles",
    "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations",
    "Ezekiel", "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
    "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians",
    "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians",
    "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus",
    "Philemon", "Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John",
    "3 John", "Jude", "Revelation",
]
BOOK_INDEX = {b: i for i, b in enumerate(BOOKS)}
OT_COUNT = BOOK_INDEX["Malachi"] + 1

_EXTRA_ALIASES = {
    # Long-form names used by some public-domain datasets. A dataset naming a
    # book in a way this table misses gets silently dropped, so ingest asserts
    # a full 66-book load rather than trusting these to be exhaustive.
    "revelation of john": "Revelation",
    "the revelation": "Revelation",
    "revelations": "Revelation",
    "song of songs": "Song of Solomon",
    "the song of songs": "Song of Solomon",
    "canticles": "Song of Solomon",
    "acts of the apostles": "Acts",
    "psalm": "Psalms",
}

def _norm(s: str) -> str:
    s = s.strip().lower().replace(".", "")
    s = re.sub(r"^(1|2|3)\s*(st|nd|rd)?\s+", r"\1 ", s)
    s = re.sub(r"^(i{1,3})\s+", lambda m: f"{len(m.group(1))} ", s)
    return re.sub(r"\s+", " ", s)

_ALIASES: dict[str, str] = {}

def _add(key: str, book: str, *, unique_only: bool = False):
    """Register an alias. `unique_only` drops keys that two books both claim."""
    key = _norm(key)
    if not key:
        return
    if key in _ALIASES:
        if unique_only and _ALIASES[key] != book:
            _ALIASES[key] = None          # poisoned: ambiguous, refuse to guess
        return
    _ALIASES[key] = book

for _b in BOOKS:
    _n = _norm(_b)
    _add(_n, _b)
    _add(_n.replace(" ", ""), _b)

# Auto-generated prefix abbreviations. A prefix is only accepted if exactly one
# book claims it — "Phi" is ambiguous (Philippians/Philemon) and is dropped
# rather than silently resolved, which is the whole point of this module.
for _b in BOOKS:
    _parts = _norm(_b).split()
    _num = _parts[0] if _parts[0].isdigit() else ""
    _word = _parts[1] if _num else _parts[0]
    for _k in range(2, 7):
        if len(_word) <= _k:
            break
        _stem = _word[:_k]
        _add(f"{_num} {_stem}".strip(), _b, unique_only=True)
        _add(f"{_num}{_stem}" if _num else _stem, _b, unique_only=True)

# Irregular abbreviations in common use that no prefix rule produces.
_EXPLICIT = {
    "mt": "Matthew", "mk": "Mark", "mr": "Mark", "lk": "Luke", "jn": "John",
    "jhn": "John", "jas": "James", "phil": "Philippians", "php": "Philippians",
    "phlm": "Philemon", "philem": "Philemon", "pss": "Psalms", "ps": "Psalms",
    "sg": "Song of Solomon", "sos": "Song of Solomon", "song": "Song of Solomon", "jgs": "Judges",
    "jdg": "Judges", "hb": "Hebrews", "rv": "Revelation", "rev": "Revelation",
    "dt": "Deuteronomy", "gn": "Genesis", "ex": "Exodus", "lv": "Leviticus",
    "nm": "Numbers", "prv": "Proverbs", "eccl": "Ecclesiastes",
}
for _k, _v in _EXPLICIT.items():
    _ALIASES[_norm(_k)] = _v

for _k, _v in _EXTRA_ALIASES.items():
    if _v:
        _ALIASES[_norm(_k)] = _v

def canonical_book(name: str) -> str | None:
    """Resolve a book name or abbreviation. Ambiguous keys resolve to None."""
    return _ALIASES.get(_norm(name))

@dataclass(frozen=True, order=False)
class Ref:
    book: str
    chapter: int
    verseStart: int
    verseEnd: int

    def __post_init__(self):
        if self.book not in BOOK_INDEX:
            raise ValueError(f"not a canonical book: {self.book!r}")

    @property
    def testament(self) -> str:
        return "OT" if BOOK_INDEX[self.book] < OT_COUNT else "NT"

    @property
    def label(self) -> str:
        tail = f"-{self.verseEnd}" if self.verseEnd != self.verseStart else ""
        return f"{self.book} {self.chapter}:{self.verseStart}{tail}"

    @property
    def sort_key(self):
        return (BOOK_INDEX[self.book], self.chapter, self.verseStart)

    def dict(self):
        return asdict(self)

_REF_RE = re.compile(
    r"^\s*([1-3]?\s*[A-Za-z][A-Za-z\s]*?)\s*(\d+)\s*[:.]\s*(\d+)\s*(?:[-–]\s*(\d+))?\s*$"
)

def parse(text: str) -> Ref | None:
    """Parse 'Philippians 4:6-7', '1 Pet 5.6', 'Ps 23:1' -> Ref, or None."""
    m = _REF_RE.match(text or "")
    if not m:
        return None
    book = canonical_book(m.group(1))
    if not book:
        return None
    start = int(m.group(3))
    end = int(m.group(4) or start)
    if end < start:
        start, end = end, start
    try:
        return Ref(book, int(m.group(2)), start, end)
    except ValueError:
        return None

# Matches inline citations the model writes, e.g. "[Philippians 4:6-7]"
INLINE_RE = re.compile(r"\[([^\[\]]{2,40}?\s\d+[:.]\d+(?:[-–]\d+)?)\]")

def find_inline(text: str) -> list[Ref]:
    out, seen = [], set()
    for raw in INLINE_RE.findall(text or ""):
        r = parse(raw)
        if r and r.label not in seen:
            seen.add(r.label)
            out.append(r)
    return out
