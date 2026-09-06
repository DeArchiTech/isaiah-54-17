"""Berean AI configuration.

Forked from ai_tutor_be. Two deliberate departures from the parent project:

1. Scripture is NOT stored as chunked PDF text. It lives verse-level in SQLite,
   because a citation must resolve to an exact canonical address. Chroma is used
   only to *find* candidate verses; it is never the source of the text shown.

2. The semantic index is built over ONE translation (the base). Translations are
   a rendering concern: you search once, then display the hit in whichever text
   the reader has selected. Indexing all three would triple the cost to return
   the same references.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("BEREAN_DATA_DIR", ROOT / "data"))

VERSE_DB = DATA_DIR / "scripture.sqlite3"
CHROMA_DB = DATA_DIR / "chroma"
COLLECTION = "verses"

BASE_TRANSLATION = "BSB"

TRANSLATIONS = {
    "BSB": {"name": "Berean Standard Bible", "note": "Public domain", "locked": False},
    "KJV": {"name": "King James Version", "note": "Public domain", "locked": False},
    "ASV": {"name": "American Standard Version", "note": "Public domain", "locked": False},
    # Present so the constraint is visible in the UI, never served.
    "ESV": {"name": "English Standard Version", "note": "Licence required", "locked": True},
    "NIV": {"name": "New International Version", "note": "Licence required", "locked": True},
    "NASB": {"name": "New American Standard", "note": "Licence required", "locked": True},
}

def open_translations():
    return [t for t, m in TRANSLATIONS.items() if not m["locked"]]

# Window size for the semantic index: a verse plus its neighbours reads better
# to an embedding model than a bare verse, but the citation stays the anchor.
WINDOW = 2
